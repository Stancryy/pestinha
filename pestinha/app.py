"""
APP - a composição: liga os sentidos, o cérebro, o corpo e os controladores.

Relógios (todos na thread do Qt):
    16 ms   física, comportamento, travessuras e desenho
    100 ms  homeostase, cérebro, emoção, protesto, sono e aprendizado
    250 ms  janelas onde ele pode pousar
    500 ms  sensores do sistema (janela ativa, ocioso, tela cheia)
    30 s    salva cérebro, homeostase, memória e protesto

Este arquivo cria tudo e roda os três ciclos. O resto mora em mixins:
    controle/sessao.py      permissões, visibilidade, pausa, pânico, salvar, sair, apagar dados
    controle/interacao.py   cutucar, arrastar, arremessar, menus e notebook

Quem faz o quê:
    sense / think / frame   leitura, decisão e desenho, nessa ordem
    SleepController         dormir e acordar
    ProtestController       estágios e cartazes
    MischiefController      quando e como apronta; o que a dispensa causa
    FloatManager            painéis de teste
    SettingsStore           permissões e pânico
    PetState                o que ele sente e mostra (lido pela janela e pelo comportamento)
"""

import math
import time

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QSystemTrayIcon

from . import ajustes
from . import config
from . import log as log_module
from . import migracao
from . import plataforma
from .ajustes import (
    ATIVIDADE_MINIMA_VOO as REFLEX_MIN_HZ,
    BATIDA_FORTE as HARD_IMPACT,
    BATIDA_TONTA as DIZZY_IMPACT,
    DURACAO_TONTURA as DIZZY_SECONDS,
    INTERVALO_BATIDA as IMPACT_COOLDOWN,
    LIMIAR_CANTO_HZ,
    INTERVALO_QUADRO_ATIVO_MS,
    INTERVALO_QUADRO_PARADO_MS,
    INTERVALO_QUADRO_DORMINDO_MS,
    PUNICAO_DISPENSA as DISMISS_PENALTY,
    RECOMPENSA_CARINHO as CARESS_REWARD,
    SILENCIO_MOUSE as MOUSE_QUIET,
)
from .body.behavior import Behavior
from .body.bolinha import Ball, load_sprite
from .body.brincadeira import Play
from .body.desenho_rosto import aparencia_de, aplicar_skin_sazonal
from .body.pet import PetWindow, cursor_pos
from .body.pet_state import PetState
from .body.toy import ToyTracker, bounce_off, push_from_cursor
from .controle.interacao import InteracaoMixin
from .controle.sessao import SessaoMixin
from .core.conditioning import Conditioning
from .core.conquistas import Conquistas
from .core.emotion import PRIORITY, EmotionState
from .core.episodic import EpisodicMemory
from .core.homeostasis import Drives
from .core.nervous_system import LIFBrain
from .core.protesto import Protesto
from .log import log
from .mind.castigo_ctl import CastigoController
from .mind.companhia import CompanhiaController
from .mind.llm_local import GeradorLLMLocal
from .mind.segundo_pet import SegundoPetController
from .mind.festa import FestaController
from .mind.mesa import MesaController, pull
from .mind.mischief_ctl import MischiefController
from .mind.protest_ctl import ProtestController
from .mind.revolucao import RevolucaoController
from .mind.sleep import SleepController
from .paths import Paths
from .sense import senses
from .sense.timeline import TimelineRecorder, fator_ciclo_rotina
from .ui.float_manager import FloatManager
from .ui.ui import PanicHotkey, Tray
from .world.mischief import MischiefEngine
from .world.som import SoundFX

MAX_DT = 2.0          # s: um atraso maior que isso (suspensão) não vira tempo de rede

SAVE_EVERY_MS = 30_000


class PestinhaApp(SessaoMixin, InteracaoMixin, QObject):
    """Aplicativo do pet: junta a rede neural, os sentidos, o corpo, as travessuras e a interface. Um único objeto, criado em main.py."""
    def __init__(self, store, paths=None):
        """Monta tudo na ordem certa: primeiro a memória e o conteúdo do pet, depois a rede, os sentidos, o corpo, a bandeja e os relógios."""
        super().__init__()
        self.store = store
        self.perms = store.perms
        self.paths = paths or Paths()
        log_module.setup(self.paths.log, self.paths.crash_log)
        ajustes.carregar_ajustes(self.paths.ajustes)
        self.prof = config.profile(self.perms)
        self.debugging = lambda: self.perms["modo_teste"]

        # ----- qual pet, e onde fica a memória dele -----
        pet_id = config.escolher_pet(self.paths, self.perms["pet"])     # só um pets/<id>.json vira personagem
        migracao_feita = migracao.migrar(self.paths, pet_id)
        if migracao_feita.pet_ok(pet_id):
            self.pet_paths = self.paths.pet(pet_id)
            self.aviso_migracao = None
        else:
            # pendência na migração: usa os arquivos antigos, como antes, e avisa (nada é perdido)
            self.pet_paths = self.paths.pet_legado(pet_id)
            self.aviso_migracao = ("A memória ainda está no formato antigo (migração pendente: "
                                   f"{migracao_feita.resumo()}). Nada foi apagado; veja memory/logs.")
            log(f"[migração] {pet_id} em modo compatível: {migracao_feita.resumo()}")

        # ----- cérebro e estado interno -----
        pet_def = config.load_pet(self.paths, pet_id)
        self.conteudo = self.paths.conteudo(pet_id)   # frases, cartazes e imagens deste pet
        self.nome = pet_def["nome"]                   # quem fala nos textos; o programa é config.APP_NOME
        self.reacao_notebook = pet_def["reacao_notebook"]     # "bravo" ou "triste": depende do pet
        self.brain = LIFBrain(seed=pet_def["seed"], temperament=pet_def.get("temperamento"))
        self.state_file = self.pet_paths.nervous
        self.brain.load(str(self.state_file))
        self.intensities = {}       # última entrada da rede (para o monitor)
        self.pulso_recusa = 0.0     # 1 quando ele recusou um pedido (vira RECUSA na rede)
        self.drives = Drives()
        self.drives.load(self.pet_paths.drives, self.prof)
        self.memory = EpisodicMemory(self.pet_paths.episodes, self.pet_paths.preferences)
        self.memory.load()
        self.emotion = EmotionState()
        self.pet_state = PetState()
        self.conditioning = Conditioning(self.pet_paths.conditioning, self.prof["cond_rate"])
        self.conditioning.load()
        self.conquistas = Conquistas(self.pet_paths.achievements)
        self.som = SoundFX()
        self._carinho_acum_s = 0.0
        self.prev_pet_dist = None
        self.protest = Protesto(self.conteudo.signs, self.pet_paths.protest)
        self.protest.load(self.prof)

        # ----- sentidos -----
        senses.carregar_atividades(self.paths.activities)
        self.senses = senses.ComputerSenses()
        self.monitor_digitacao = plataforma.obter_monitor_digitacao()
        self.monitor_digitacao.iniciar()
        self.tracker = senses.ActivityTracker()
        self.activity = "IDLE"
        self._active_app_name = ""
        self.dnd_manual = False
        self.fator_ciclo = 1.0
        self.idle_seconds = 0.0
        self.fullscreen = False
        self.platforms = []
        self.keyboard_active = False
        self.last_cursor = (0, 0)
        self.mouse_moved_at = 0.0
        self.timeline = TimelineRecorder(self.paths.timeline, lambda: self.perms["rotina"])

        # ----- corpo e travessuras -----
        left, top, right, _bottom = self.bounds()
        self.pet = PetWindow(right - 220, top + 120, self.pet_state)
        self._aparencia_base = aparencia_de(pet_def.get("aparencia"))
        self.pet.aparencia = aplicar_skin_sazonal(self._aparencia_base, bool(self.perms.get("skins_sazonais", False)))
        self.pet.poked.connect(self.on_poke)
        self.pet.drag_started.connect(self.on_drag_started)
        self.pet.drag_ended.connect(lambda: self.senses.set_dragging(False))
        self.pet.thrown.connect(self.on_thrown)
        self.pet.menu_requested.connect(self.show_pet_menu)
        self.ball_stored = False    # você guardou a bolinha pelo menu
        self.mischief = MischiefEngine(self.conteudo)
        self.llm = GeradorLLMLocal()
        self.mischief.gerador_nota = lambda emocao, notes: self.llm.escolher_frase(
            notes,
            ativo=bool(self.perms.get("llm_local", False)),
            endpoint=self.perms.get("llm_endpoint", ""),
            modelo=self.perms.get("llm_modelo", ""),
            nome_pet=self.nome,
            emocao=emocao,
            atividade=self.activity,
        )
        self.segundo_pet = SegundoPetController(self.paths, pet_id)
        self.mischief.dismissed.connect(self.on_dismissed)
        self.behavior = Behavior(self.pet.body, self.pet_state, self.mischief)

        # ----- controladores -----
        self.sleep = SleepController(self.emotion, self.drives, self.memory, self.debugging)
        self.protest_ctl = ProtestController(self.protest, self.pet.body, self.behavior,
                                             self.senses, self.drives, self.pet_state, self.debugging)
        self.sad = Protesto(self.conteudo.signs, self.pet_paths.sad_protest, kind="tristeza")
        self.sad.load(self.prof)
        self.sad_ctl = ProtestController(self.sad, self.pet.body, self.behavior,
                                         self.senses, self.drives, self.pet_state, self.debugging)
        self.ball = Ball(left + 400, self.bounds()[3] - 40, sprite=load_sprite(self.conteudo.bolinha_tenis))
        self.play_weights = pet_def.get("brincadeira", None)
        self.behavior.ball = self.ball
        self.behavior.play = Play(self.play_weights)
        self.toy_tracker = ToyTracker()
        self.cursor_vel = (0.0, 0.0)
        self._prev_cursor = None
        self._prev_cursor_t = 0.0
        self.last_cursor_push = -1e9
        self.mischief_ctl = MischiefController(self.mischief, self.memory, self.drives, self.senses,
                                               self.behavior, self.emotion, self.debugging)
        self.floats = FloatManager(self)
        self.mischief_ctl.postit_weight = Play(self.play_weights).weight("postit")
        self.festa = FestaController(self.debugging)
        self.mesa = MesaController(self.debugging, self)
        self.companhia = CompanhiaController(self)
        self.castigo = CastigoController(self, self.debugging)
        paper = load_sprite(self.conteudo.bolinha_papel)
        self.revolucao = RevolucaoController(self.behavior.play, self.debugging, sprite=paper, state=self.pet_state)

        # ----- reflexos e medições -----
        self.in_flight = False      # voando depois de um arremesso
        self.last_impact = 0.0
        self.last_poke = 0.0
        self.poke_probe = None      # (quando medir, CHEER antes da cutucada)
        self.last_poke_response = None

        # ----- interface -----
        self.settings = None
        self.tray = Tray(self.nome)
        self.tray.open_settings.connect(self.open_settings)
        self.tray.open_diary.connect(self.open_diary)
        self.tray.open_monitor.connect(lambda: self.floats.open("neural"))
        self.tray.open_panel.connect(lambda: self.floats.open("greve"))
        self.tray.toggle_floating.connect(self.toggle_floating)
        self.tray.toggle_pause.connect(self.toggle_pause)
        self.tray.toggle_dnd.connect(self.toggle_dnd)
        self.tray.toggle_hidden.connect(self.toggle_hidden)
        self.tray.clear_things.connect(self.clear_things)
        self.tray.panic.connect(self.panic)
        self.tray.quit.connect(self.quit)
        atalho_cfg = self.perms.get("atalho_panico", config.PANIC_HOTKEY_TEXT)
        if atalho_cfg != config.PANIC_HOTKEY_TEXT:
            try:
                self.hotkey = PanicHotkey(atalho_cfg)
            except TypeError:
                self.hotkey = PanicHotkey()
        else:
            self.hotkey = PanicHotkey()
        self.hotkey.pressed.connect(self.panic)
        self.wiping = False         # True depois de "apagar tudo": não grava mais nada ao sair
        self.paused = False
        self._pausado_em = None         # quando a pausa começou (para descontar do tempo dos episódios)
        self._ultimo_think = None       # quando a rede foi integrada pela última vez
        self.hidden = False

        # ----- relógios -----
        self.last_frame = time.monotonic()
        self.frame_timer = self._timer(INTERVALO_QUADRO_ATIVO_MS, self.frame)
        self._timer(100, self.think)
        self._timer(250, self.scan_windows)
        self._timer(500, self.sense)
        self._timer(SAVE_EVERY_MS, self.save)

        self._apply_settings()
        self.sense()
        self.scan_windows()
        problems = config.check_assets(self.conteudo)
        for text in problems:
            log(f"[assets] {text}")
        if self.aviso_migracao:
            problems.append(self.aviso_migracao)
        if not self.hotkey.ok:
            problems.append(f"atalho de pânico {atalho_cfg} já está em uso por outro programa")
        if problems:
            self.tray.icon.showMessage(config.APP_NOME,"\n".join(problems), QSystemTrayIcon.Warning, 6000)
        if self.perms["ativo"]:
            self.tray.icon.showMessage(
                self.nome, f"Estou aqui. Pânico: {atalho_cfg}",
                QSystemTrayIcon.Information, 3000,
            )

    def _timer(self, ms, slot):
        """Cria um relógio que chama `slot` a cada `ms` milissegundos."""
        timer = QTimer(self)
        timer.timeout.connect(slot)
        timer.start(ms)
        return timer

    @property
    def asleep(self):
        """Diz se o pet está dormindo."""
        return self.sleep.asleep

    # ---------------- geometria ----------------

    def screen_bounds(self):
        """Áreas úteis de todos os monitores, em coordenadas lógicas globais do Qt."""
        return [(g.x(), g.y(), g.x() + g.width(), g.y() + g.height())
                for g in (screen.availableGeometry() for screen in QGuiApplication.screens())]

    def screen_geometries(self):
        """Geometria física das telas, na mesma ordem de screen_bounds()."""
        return [(g.x(), g.y(), g.x() + g.width(), g.y() + g.height())
                for g in (screen.geometry() for screen in QGuiApplication.screens())]

    def _bounds_at(self, areas, x, y):
        """Área útil do monitor que contém o ponto, inclusive sobre barras reservadas pelo sistema."""
        if x is not None:
            encontrada = next((a for a in areas if a[0] <= x < a[2] and a[1] <= y < a[3]), None)
            if encontrada is not None:
                return encontrada
            for area, geometria in zip(areas, self.screen_geometries()):
                if geometria[0] <= x < geometria[2] and geometria[1] <= y < geometria[3]:
                    return area
        g = QGuiApplication.primaryScreen().availableGeometry()
        return g.x(), g.y(), g.x() + g.width(), g.y() + g.height()

    def bounds(self):
        """Área útil do monitor onde está o pet; usa a tela principal antes de ele ser criado."""
        if hasattr(self, "pet"):
            return self._bounds_at(self.screen_bounds(), self.pet.body.x, self.pet.body.y)
        g = QGuiApplication.primaryScreen().availableGeometry()
        return g.x(), g.y(), g.x() + g.width(), g.y() + g.height()

    def _screens_info(self):
        """Lista [((left, top, right, bottom), dpr)] de todos os monitores conectados."""
        out = []
        for s in QGuiApplication.screens():
            g = s.geometry()
            out.append(((g.x(), g.y(), g.x() + g.width(), g.y() + g.height()), s.devicePixelRatio() or 1.0))
        return out

    def _retangulo_logico(self, rect):
        """Converte (l, t, r, b) físicos em coordenadas lógicas usando o DPI do monitor da janela."""
        l, t, r, b = rect
        mx, my = (l + r) / 2, (t + b) / 2
        infos = self._screens_info()
        for (gl, gt, gr, gb), dpr in infos:
            lx, ly = mx / dpr, my / dpr
            if gl <= lx < gr and gt <= ly < gb:
                return l / dpr, t / dpr, r / dpr, b / dpr
        dpr = infos[0][1] if infos else 1.0
        return l / dpr, t / dpr, r / dpr, b / dpr

    def scan_windows(self):
        """Barras de título onde ele pode pousar, em coordenadas lógicas do Qt."""
        if not self.perms["pousar_janelas"] or not self.pet.isVisible():
            self.platforms = []
            return
        infos = self._screens_info()
        dpr = infos[0][1] if infos else 1.0
        geometrias = [g for g, _ in infos]
        exclude = {int(self.pet.winId())} | {int(t.winId()) for t in self.mischief.things}
        exclude |= self.floats.visible_handles()
        exclude |= {int(w.winId()) for w in self.revolucao.janelas()}
        exclude |= {int(w.winId()) for w in self.protest_ctl.sign_windows()}
        exclude |= {int(w.winId()) for w in self.sad_ctl.sign_windows()}
        if self.ball.isVisible():
            exclude.add(int(self.ball.winId()))
        if self.segundo_pet.janela and self.segundo_pet.janela.isVisible():
            exclude.add(int(self.segundo_pet.janela.winId()))
        above = []
        platforms = []
        for hwnd, (l, t, r, b), maximized in senses.list_windows(exclude, dpr):
            l, t, r, b = self._retangulo_logico((l, t, r, b))
            mid = (l + r) / 2
            covered = any(al <= mid <= ar and at <= t + 2 <= ab for al, at, ar, ab in above)
            above.append((l, t, r, b))
            if maximized or covered:
                continue
            if not any(gl <= mid <= gr and gt + 40 <= t <= gb - 100 for gl, gt, gr, gb in geometrias):
                continue
            platforms.append((hwnd, l + 10, r - 10, t))
        self.platforms = platforms
        if self.perms.get("pousar_barra_tarefas", True):
            self.platforms.extend(self.plataformas_barra_tarefas())

    def plataformas_barra_tarefas(self):
        """Plataformas correspondentes à borda da barra de tarefas de cada monitor."""
        barras = []
        for idx, (area, geom) in enumerate(zip(self.screen_bounds(), self.screen_geometries())):
            al, at, ar, ab = area
            gl, gt, gr, gb = geom
            if ab < gb:
                barras.append((f"taskbar_{idx}", al + 10, ar - 10, ab))
            elif at > gt:
                barras.append((f"taskbar_top_{idx}", al + 10, ar - 10, at))
        return barras

    # ---------------- relógios ----------------

    def sense(self):
        """Leitura de 500 em 500 ms: programa em primeiro plano, ocioso, janelas e tela cheia."""
        if self._congelado():
            return
        dnd_antes = self.em_nao_perturbe
        self.idle_seconds = senses.get_idle_seconds()
        app = senses.get_active_app()
        self._active_app_name = (app or "").lower()
        agora_s = time.monotonic()
        if agora_s - getattr(self, "_fator_ciclo_em", -1e9) >= 600.0:      # relê a rotina a cada 10 min, não a cada 0,5 s
            self._fator_ciclo_em = agora_s
            self.fator_ciclo = fator_ciclo_rotina(self.paths.timeline) if self.perms.get("rotina", True) else 1.0
        if self.perms.get("reagir_hardware", False):
            cpu_pct, ram_pct = senses.get_hardware_usage()
            self.pet_state.suando = cpu_pct >= ajustes.LIMIAR_CPU_ALTA
            self.pet_state.apertado = ram_pct >= ajustes.LIMIAR_RAM_ALTA
        else:
            self.pet_state.suando = False
            self.pet_state.apertado = False
        if self.perms.get("reagir_musica", False) and not self.asleep and not self.em_nao_perturbe:
            if agora_s - getattr(self, "_musica_em", -1e9) >= 5.0:          # lista de processos só a cada 5 s
                self._musica_em = agora_s
                self.pet_state.dancando = bool(senses.is_media_playing(self._active_app_name))
        else:
            self.pet_state.dancando = False
        self.activity = senses.detect_activity(app, self.idle_seconds, self.prof["away_after"])
        events = self.tracker.observe(app, self.activity)
        self.senses.on_events(events)
        for event in events:
            if event == "APP_CHANGED":
                self.drives.stimulate("app")
            elif event in ("ACTIVITY_CHANGED", "USER_RETURNED"):
                self.drives.stimulate("novelty")
        if self.perms["rotina"]:
            self.timeline.observe(
                self.activity, self.idle_seconds, events, self.tracker.session_seconds, self.keyboard_active
            )
        if "APP_CHANGED" in events or "ACTIVITY_CHANGED" in events:
            dpr = QGuiApplication.primaryScreen().devicePixelRatio()
            rect = senses.foreground_rect(dpr)
            if rect:
                lx, ly, lr, lb = self._retangulo_logico(rect)
                self.behavior.look_at((lx + lr) / 2, (ly + lb) / 2, time.monotonic())
            self.pet.manter_no_topo()
        elif agora_s - getattr(self, "_ultimo_reforco_topo", 0.0) >= 1.5:
            self._ultimo_reforco_topo = agora_s
            self.pet.manter_no_topo()


        fullscreen = senses.is_fullscreen()
        if fullscreen:
            areas = self.screen_bounds()
            if len(areas) > 1:
                rect_fs = senses.foreground_rect(1.0)
                if rect_fs:
                    lx, ly, lr, lb = self._retangulo_logico(rect_fs)
                    fs_bounds = self._bounds_at(areas, (lx + lr) / 2, (ly + lb) / 2)
                    if self.bounds() != fs_bounds:
                        fullscreen = False
        if fullscreen != self.fullscreen or self.em_nao_perturbe != dnd_antes:
            self.fullscreen = fullscreen
            self.update_visibility()

    def think(self):
        """Passo da rede (100 ms): recebe os sentidos, decide o motor vencedor e aplica no comportamento."""
        if self._congelado():
            return
        now = time.monotonic()
        dt = min(MAX_DT, max(0.0, now - self._ultimo_think)) if self._ultimo_think is not None else 0.1
        self._ultimo_think = now
        st = self.pet_state
        body = self.pet.body
        caressing = self.perms["carinho"] and self.pet.isVisible() and st.caressing(now)

        # teclado x mouse: o sistema só dá "último input"; separamos olhando se o cursor andou
        idle = senses.get_idle_seconds()
        cursor = cursor_pos()
        dist_cursor = math.hypot(cursor[0] - self.last_cursor[0], cursor[1] - self.last_cursor[1])
        mouse_vel_px_s = (dist_cursor / dt) if dt > 0 else 0.0
        fator_mouse = senses.calcular_fator_mouse(mouse_vel_px_s)

        if dist_cursor > 2:
            self.mouse_moved_at = now
        self.last_cursor = cursor
        mouse_moving = now - self.mouse_moved_at < MOUSE_QUIET
        self.keyboard_active = idle < 0.3 and not mouse_moving and not caressing

        moving = min(1.0, abs(body.vx) / 200.0 + (0.0 if body.grounded else 1.0))
        self.drives.update(dt, self.prof, self.asleep, moving, self.emotion.arousal,
                           self.activity == "AWAY", engaged=self.activity in ("PROGRAMMING", "DESIGNING"),
                           preso=self.castigo.dentro, visitado=self.castigo.visita > 0.5,
                           fator_ciclo=getattr(self, "fator_ciclo", 1.0))
        self.castigo.tick_lento(dt)
        if caressing:
            self.drives.stimulate("caress", dt)
            self.drives.touched("caress", dt)
            self.memory.on_interaction()
            self._carinho_acum_s += dt
            if self._carinho_acum_s >= 1.0:
                self._carinho_acum_s -= 1.0
                self.registrar_conquista("carinhos", 1)
                self.tocar_som("carinho")

        # novos canais sensoriais expandidos
        teclas_s = self.monitor_digitacao.teclas_por_segundo() if hasattr(self, "monitor_digitacao") else 0.0
        fator_digitacao = senses.calcular_fator_digitacao(teclas_s)
        cpu_pct, _ram_pct = senses.get_hardware_usage()
        fator_cpu = cpu_pct / 100.0
        bat_pct, bat_plugged = plataforma.bateria_status()
        fator_bateria = senses.calcular_fator_bateria(bat_pct, bat_plugged)
        fator_janelas = senses.calcular_fator_janelas(len(self.platforms))
        fator_circadiano = senses.calcular_fator_circadiano()

        intensities = self.senses.update(
            self.activity, idle, self.drives.channels(), caressing, mouse_moving,
            typing_speed=fator_digitacao,
            cpu_load=fator_cpu,
            circadian=fator_circadiano,
            mouse_speed=fator_mouse,
            battery_low=fator_bateria,
            window_count=fator_janelas,
        )
        st.torcendo = (fator_digitacao >= 0.7) and not getattr(self.pet_state, "at_desk", False)
        st.bateria_baixa = fator_bateria >= 0.5
        st.corujao = fator_circadiano >= 0.7
        if self.perms.get("reagir_hardware", False):
            st.suando = cpu_pct >= ajustes.LIMIAR_CPU_ALTA
            st.apertado = _ram_pct >= ajustes.LIMIAR_RAM_ALTA
        else:
            st.suando = False
            st.apertado = False
        if getattr(self.pet_state, "dancando", False):
            intensities["SOUND"] = max(intensities.get("SOUND", 0.0), 0.75)
        # condicionamento: o cursor vindo rápido para ele, ou o botão apertado em cima, antecipam
        dist = math.hypot(cursor[0] - body.x, cursor[1] - body.y)
        if fator_mouse >= 0.8 and dist < 220:
            self.senses.kick("MOTION", 0.4)
        approaching = (self.prev_pet_dist is not None and dist < 220
                       and dt > 0 and (self.prev_pet_dist - dist) / dt > 500)
        self.prev_pet_dist = dist
        self.conditioning.set_cue("PRESS", st.pressing, now)
        self.conditioning.set_cue("APPROACH", approaching, now)
        self.conditioning.set_cue("PLACA", self.castigo.perto_da_placa(body), now)
        self.conditioning.tick(now)
        intensities["ANTICIPATE"] = self.conditioning.strength()                     # cutucada, arraste
        intensities["ANTECIPA_PLACA"] = self.conditioning.strength(cues=("PLACA",))  # ir para o canto
        # bolinha: perto dele brinca; se você levou para longe, ele sente
        ball_xy = (self.ball.body.x, self.ball.body.y)
        taken, near = self.toy_tracker.update(ball_xy, (body.x, body.y), self.ball.handled_by_user(now))
        if taken and self.perms["bolinha"] and not self.ball_stored:
            self.senses.kick("TOY_TAKEN", 0.9)
        intensities["TOY_NEAR"] = near if self.perms["bolinha"] and not self.ball_stored else 0.0
        # sinais de estado: o pedido seu, o cantinho, a memória de fugas e a recusa
        intensities["PEDIDO"] = self.mesa.intensidade_pedido(now)
        intensities.update(self.castigo.sinais(body))  # preso, memória de fuga, placa, visita, receio, rancor
        intensities["RECUSA"] = self.pulso_recusa
        self.pulso_recusa = 0.0
        total_ms = max(1, round(dt * 1000))
        while total_ms > 0:
            chunk = min(100, total_ms)
            self.brain.stimulate(intensities)
            self.brain.step(chunk)
            total_ms -= chunk
        self.intensities = intensities
        motor = self.brain.motor_activity()
        st.tone.update(motor, dt)

        change = self.protest_ctl.tick(dt, st.tone, self.prof, caressing, now)
        if change:
            self.protest_ctl.on_stage(*change)
            if change[1] == 4:
                self.registrar_conquista("revolucoes", 1)
                self.tocar_som("protesto")
        sad_change = self.sad_ctl.tick(dt, st.tone, self.prof, caressing, now,
                                       self.drives.channels()["LONELY"])
        if sad_change:
            self.sad_ctl.on_stage(*sad_change)
        if self.asleep:
            st.protest_stage = 0
        elif self.protest.stage:
            st.protest_stage = self.protest.stage
        else:
            st.protest_stage = 3 if self.sad.stage >= 2 else 0     # abandonado: fica sentado, quieto
        if self.poke_probe and now >= self.poke_probe[0]:
            self.poke_reflex(motor["CHEER"] - self.poke_probe[1])

        reward = 0.0
        if self.perms["carinho"] and not self.protest.stage:     # em protesto, carinho acalma mas não ensina
            if caressing:
                reward += CARESS_REWARD
            if self.mischief_ctl.penalty_active(now):
                reward += DISMISS_PENALTY
        reward += self.castigo.punicao(now)          # ser preso é recompensa negativa: o castigo ensina
        self.brain.learn(reward, dt, self.prof["learn_rate"])

        if self.in_flight:
            if body.grounded:
                self.in_flight = False
            else:
                # reflexo no ar: o que estiver mais ativo na rede agora decide a cara
                rates = self.brain.pool_rates()
                reflex, hz = max(
                    (("feliz", rates["PLAYFUL"]), ("assustado", rates["ALERT"]), ("bravo", rates["FRUSTRATION"])),
                    key=lambda item: item[1],
                )
                if hz < REFLEX_MIN_HZ:
                    reflex = "feliz"        # rede ainda quieta: voar é divertido
                self.emotion.force(reflex, 0.3, now, PRIORITY["voo"])
        if caressing:
            self.emotion.force("contente", 0.5, now, PRIORITY["carinho"])     # fecha os olhinhos na hora
            self.timeline.note_interaction(dt)

        self.sleep.tick(now, body, self.in_flight, self.protest.stage, self.behavior.mission)

        emotion = self.emotion.update(motor, dt, self.prof)
        if self.protest.stage >= 2 and not self.asleep:
            self.emotion.force("bravo", 0.3, now, PRIORITY["protesto"])     # cara de raiva na manifestação
            emotion = self.emotion.update(motor, 0.0, self.prof)
        elif self.sad.stage >= 2 and not self.asleep:
            self.emotion.force("triste", 0.3, now, PRIORITY["protesto"])    # abandonado: cara triste
            emotion = self.emotion.update(motor, 0.0, self.prof)
        self.timeline.note_emotion(emotion, dt)
        self.festa.tick(now, motor, emotion, self.pet.body, self._pode_soltar_fogo(), dt)
        self._atualizar_mesa(now)
        self.companhia.tick(now, dt)
        self.memory.tick(now, self.prof["episode_ok"], self.prof["episode_window"])
        st.emotion = emotion
        self.behavior.on_emotion(emotion, time.monotonic())

    def frame(self):
        """Um quadro da tela: move o corpo pela física e atualiza a animação do pet."""
        now = time.monotonic()
        dt = min(0.05, max(0.0, now - self.last_frame))
        self.last_frame = now
        if not self.pet.isVisible() or self.paused or self.wiping:
            return

        areas = self.screen_bounds()
        monitores = self.screen_geometries()
        bounds = self.bounds()
        cursor = cursor_pos()
        body = self.pet.body
        body.step(dt, bounds, self.platforms, areas, monitores)
        self.behavior.screen_areas = areas
        if not body.held and self.mesa.pin(body, now) == "arrancado":
            self.pet_state.definir_acao("arrancada_notebook", 0.8, now)
            self.arrancar_notebook(now)
        speed = max(body.pop_impacts(), default=0.0)
        if speed >= HARD_IMPACT and now - self.last_impact >= IMPACT_COOLDOWN:
            self.pet_state.definir_acao("quique", 0.35, now)
            self.last_impact = now
            self.senses.impact(min(1.0, 0.3 + (speed - HARD_IMPACT) / 1500.0))
            if self.asleep:
                self.sleep.wake(startled=True)
            if speed >= DIZZY_IMPACT:
                self.pet_state.dizzy_until = now + DIZZY_SECONDS
        motores = self.brain.motor_activity()
        self.behavior.canto = motores["CANTO"] >= LIMIAR_CANTO_HZ
        self.behavior.tick(dt, now, cursor, bounds, self.prof, self.platforms)
        self.castigo.act(now, body, bounds, cursor, self.pet_state, motores, asleep=self.asleep)
        preso = self.castigo.dentro                  # no cantinho, nada de greve
        if self.protest.stage == 0:
            self.sad_ctl.carry(now, self.asleep or preso)
        else:
            self.sad_ctl.drop_sign()
        self.protest_ctl.carry(now, self.asleep or preso)
        ball_bounds = self._bounds_at(areas, self.ball.body.x, self.ball.body.y)
        self.ball.step(dt, ball_bounds, areas, monitores)
        self.revolucao.tick(
            now, dt, bounds, cursor, self.cursor_vel, self.pet.body, self.pet.isVisible(),
            revoltado=self.protest.stage == 4 and not self.asleep and not preso and self.pet.isVisible(),
            papel_hz=motores["PAPEL"],
            obstaculos=self._obstaculos_da_mesa(),
        )
        # o cursor também bate na bolinha
        if self._prev_cursor is not None and now > self._prev_cursor_t:
            k = now - self._prev_cursor_t
            self.cursor_vel = ((cursor[0] - self._prev_cursor[0]) / k, (cursor[1] - self._prev_cursor[1]) / k)
        self._prev_cursor, self._prev_cursor_t = cursor, now
        self.last_cursor_push = push_from_cursor(self.ball, cursor, self.cursor_vel, now, self.last_cursor_push)
        bounce_off(self.ball, [(g.x(), g.y(), g.width(), g.height())
                               for g in (t.geometry() for t in self.mischief.things if not t.carried)])
        self.behavior.toy = (self.ball.body.x, self.ball.body.y) if self.ball.isVisible() else None
        self.mischief.tick(dt, bounds[3])
        self.pet.animate(now)
        self.segundo_pet.tick(
            dt, now, bounds, areas, monitores, self.platforms,
            self.pet, self.pet_state, self.drives, self.ball,
        )
        self.maybe_mischief(now, dt, bounds, cursor, motores)
        self._ajustar_fps()

    def _ajustar_fps(self):
        """FPS adaptativo: ~60 fps em movimento, ~20 fps parado em repouso, ~5 fps dormindo."""
        if not hasattr(self, "frame_timer"):
            return
        body = self.pet.body
        bola_parada = not self.ball.isVisible() or (
            self.ball.body.grounded and not self.ball.dragging and abs(self.ball.body.vx) < 2.0 and abs(self.ball.body.vy) < 2.0
        )
        objetos_parados = all(t.resting and not t.carried for t in self.mischief.things)
        pet_parado = body.grounded and not body.held and abs(body.vx) < 2.0 and abs(body.vy) < 2.0 and not self.behavior.mission
        janela2 = self.segundo_pet.janela if hasattr(self, "segundo_pet") else None
        if janela2 is not None and janela2.isVisible():
            b2 = janela2.body
            pet_parado = pet_parado and b2.grounded and abs(b2.vx) < 2.0 and abs(b2.vy) < 2.0 and self.segundo_pet.alvo_x is None
        if self.asleep and pet_parado and bola_parada and objetos_parados:
            alvo = INTERVALO_QUADRO_DORMINDO_MS
        elif pet_parado and bola_parada and objetos_parados and self.protest.stage < 4:
            alvo = INTERVALO_QUADRO_PARADO_MS
        else:
            alvo = INTERVALO_QUADRO_ATIVO_MS
        if self.frame_timer.interval() != alvo:
            self.frame_timer.setInterval(alvo)

    def _atualizar_mesa(self, now):
        """O neurônio SENTAR decide se ele senta no notebook. Aqui só entram as condições do corpo."""
        rates = self.brain.pool_rates()
        motores = self.brain.motor_activity()
        pode_sentar = (not self.asleep and self.pet.body.grounded and not self.pet.body.held
                       and not self.behavior.mission and not self.in_flight
                       and not self.castigo.dentro and self.castigo.fuga is None
                       and not self.mesa.escondido
                       and self.activity != "GAMING")   # preso, fugindo, notebook escondido ou em jogo não senta
        self.mesa.tick(now, rates, motores["SENTAR"], pode_sentar, self.behavior.play)
        self.pet_state.at_desk = self.mesa.sentado
        self.pet_state.desk_top = self.mesa.caderno.y() if self.mesa.sentado else None
        self.behavior.play_pull = pull(rates)
        if self.mesa.pop_recusa():                 # pediram para trabalhar e ele não quis
            self.pulso_recusa = min(1.0, 0.4 + 0.2 * self.mesa.pedidos_recentes())
            if self.debugging():
                log(f"[notebook] recusou o pedido (pedidos recentes: {self.mesa.pedidos_recentes()})")

    def _pode_soltar_fogo(self):
        """Diz se pode soltar fogos de artifício agora (permitido, acordado e pet visível)."""
        return self.perms["fogos"] and not self.asleep and self.pet.isVisible()

    def _obstaculos_da_mesa(self):
        """Retângulos dos post-its e objetos, onde a bolinha de papel bate."""
        return [(g.x(), g.y(), g.width(), g.height())
                for g in (t.geometry() for t in self.mischief.things if not t.carried)]

    def maybe_mischief(self, now, dt, bounds, cursor, motores):
        """Decide se vai aprontar uma travessura agora (não aprontar de castigo nem dormindo)."""
        if self.castigo.dentro or self.em_nao_perturbe:  # de castigo ou em Não Perturbe não apronta
            return
        self.mischief_ctl.maybe_act(
            now, dt, bounds, cursor, self.pet.body, motores=motores,
            activity=self.activity, emotion=self.pet_state.emotion, perms=self.perms, prof=self.prof,
            fullscreen=self.fullscreen, asleep=self.asleep, protest_stage=self.protest.stage,
            working=self.activity in ("PROGRAMMING", "DESIGNING") and not self.mesa.sentado,
        )

    # ---------------- interação ----------------

    # ---------------- controles ----------------

    # ---------------- menu do botão direito ----------------

