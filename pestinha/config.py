"""
CONFIG - caminhos, permissões da sessão, perfis de tempo e pets.

Tudo o que o usuário escolhe na tela inicial mora em memory/permissions.json (ver paths.py)
e é gravado a CADA mudança (se o programa cair, a escolha não se perde).
"""

import random

from .paths import pet_id_valido
from .store import read_json, read_lines, write_json

EMOTIONS = ["feliz", "contente", "observando", "curioso", "bravo", "triste", "assustado", "dramatico"]

EMOTION_NAMES = {
    "feliz": "FELIZ",
    "contente": "CONTENTE",
    "observando": "OBSERVANDO",
    "curioso": "CURIOSO",
    "bravo": "BRAVO",
    "triste": "TRISTE",
    "assustado": "ASSUSTADO",
    "dramatico": "DRAMÁTICO",
    "dormindo": "DORMINDO",
}

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

PANIC_HOTKEY_TEXT = "Ctrl + Alt + Shift + B"

# ============================================================
# PERMISSÕES
# ============================================================

DEFAULT_PERMISSIONS = {
    "ativo": True,             # False depois do pânico, até religar na tela inicial
    "pet": "mia",
    "travessuras": False,      # interruptor mestre de memes/fotos/bilhetes
    "memes": True,
    "fotos": False,
    "bilhetes": True,
    "cutucar": True,
    "carinho": True,           # esfregar o mouse nele = carinho, e ele aprende com isso
    "arrastar": True,
    "pousar_janelas": True,
    "tela_cheia": False,       # experimental: aparecer em jogo/vídeo/apresentação
    "rotina": True,            # grava a timeline por minuto (só categorias) para o LSTM
    "modo_teste": False,       # desligado por padrão: o modo teste é só para desenvolvimento
    "mostrar_emocao": False,   # só vale com modo_teste ligado
    "bolinha": True,           # a bolinha para ele brincar
    "fogos": True,             # fogo de artifício quando ele fica feliz de verdade (rede)
    "nao_perturbe_auto": True, # pausa travessuras e bolinha em jogos, tela cheia ou reuniões
    "iniciar_windows": False,  # cria/remove atalho na pasta Inicializar do Windows
    "atalho_panico": PANIC_HOTKEY_TEXT,
    "pousar_barra_tarefas": True,
    "reagir_hardware": False,  # opt-in: reage a CPU/RAM altas (suando/apertado)
    "reagir_musica": False,    # opt-in: dança quando há música/mídia tocando
    "lembretes_saude": False,  # opt-in: lembretes leves de água e postura
    "comemorar_commits": False, # opt-in: comemora commits locais do Git (só mtime)
    "git_repo_path": "",       # pasta do repositório Git monitorado (vazio = pasta atual)
}

# (chave, rótulo, descrição) na ordem da tela inicial
PERMISSION_GROUPS = [
    ("Travessuras", [
        ("travessuras", "Travessuras", "Interruptor geral: sem ele, nada de memes, fotos ou bilhetes."),
        ("memes", "Trazer memes", "Imagens de pets/<pet>/memes/<emoção>/."),
        ("fotos", "Trazer fotos", "Imagens de assets/comum/fotos/."),
        ("bilhetes", "Deixar bilhetes", "Post-its com frases de pets/<pet>/recadinhos.txt."),
    ]),
    ("Interação", [
        ("cutucar", "Cutucar", "Clicar nele é uma cutucada, e ele reage."),
        ("carinho", "Carinho e aprendizado",
         "Passar o mouse para lá e para cá em cima dele é carinho. Ele aprende a gostar "
         "do que estava acontecendo quando ganhou carinho (e a desgostar de ser dispensado)."),
        ("arrastar", "Arrastar e arremessar", "Segurar, girar com a rodinha e jogar longe."),
        ("pousar_janelas", "Pousar em janelas", "Solto no ar, ele pode cair em cima da barra de título."),
        ("pousar_barra_tarefas", "Andar e pousar na barra de tarefas",
         "Usa a borda da barra de tarefas como plataforma para caminhar e pousar."),
    ]),
    ("Contexto", [
        ("tela_cheia", "Aparecer em tela cheia (experimental)",
         "Por padrão ele some em jogos, vídeos e apresentações."),
        ("nao_perturbe_auto", "Modo Não Perturbe automático",
         "Em jogos, tela cheia ou reuniões (Zoom, Teams, Meet), pausa travessuras e esconde a bolinha."),
        ("iniciar_windows", "Iniciar junto com o Windows",
         "Cria um atalho silencioso na pasta Inicializar do usuário (abre direto na bandeja)."),
        ("reagir_hardware", "Sentir uso de CPU e RAM (opcional)",
         "CPU alta faz o pet suar; RAM cheia deixa ele apertado. Desligado por padrão."),
        ("reagir_musica", "Dançar com música tocando (opcional)",
         "Reage apenas ao estado tocando/pausado de players de música, sem nunca ler títulos. Desligado por padrão."),
        ("lembretes_saude", "Lembretes leves de água e postura (opcional)",
         "Sugere beber água e relaxar os ombros sem culpar nem pressionar. Desligado por padrão."),
        ("comemorar_commits", "Comemorar commits do Git (opcional)",
         "Comemora quando a data de .git/logs/HEAD muda (nunca lê código nem mensagem de commit). Desligado por padrão."),
    ]),
    ("Rotina", [
        ("rotina", "Aprender minha rotina",
         "Grava 1 linha por minuto em memory/timeline.csv: hora, categoria de atividade, "
         "trocas de programa, ocioso. Nunca títulos, sites ou conteúdo."),
    ]),
    ("Brincadeira", [
        ("fogos", "Fogos de artifício", "Quando ele fica muito feliz, a alegria da rede pode soltar um fogo."),
        ("bolinha", "Bolinha", "Uma bolinha para ele brincar. Se você levar para longe, ele reage (pode ficar triste, bravo ou ir atrás)."),
    ]),
    ("Teste", [
        ("modo_teste", "Modo teste", "Tempos curtos: travessuras e emoções acontecem em segundos."),
        ("mostrar_emocao", "Mostrar nome da emoção", "Texto pequeno embaixo dele (só no modo teste)."),
    ]),
]


def permissoes_validas(novo):
    """Mantém só as chaves conhecidas e com o mesmo tipo do padrão."""
    return {k: v for k, v in novo.items()
            if k in DEFAULT_PERMISSIONS and type(v) is type(DEFAULT_PERMISSIONS[k])}


def load_permissions(paths):
    """Lê as permissões salvas e completa as que faltam com o padrão (um arquivo antigo continua valendo)."""
    perms = dict(DEFAULT_PERMISSIONS)
    saved = read_json(paths.permissions, default=None)
    if isinstance(saved, dict):
        perms.update(permissoes_validas(saved))
    return perms


def save_permissions(paths, perms):
    """Grava as permissões em memory/permissions.json."""
    write_json(paths.permissions, perms, indent=1)


# ============================================================
# PERFIS DE TEMPO (segundos)
# ============================================================

PROFILES = {
    "teste": {
        "mischief_interval": (20.0, 45.0),
        "max_objects": 3,
        "emotion_tau": 1.5,          # quão rápido a emoção segue o cérebro
        "emotion_dwell": 0.6,        # tempo mínimo numa emoção
        "roam_interval": (2.0, 5.0),
        "drama_window": 15.0,
        "drama_count": 3,
        "away_after": 10.0,
        "righting_after": 3.0,       # tempo tombado antes de tentar levantar
        "learn_rate": 0.004,         # ~5 s de carinho já mudam uma associação
        "cond_rate": 0.12,           # condicionamento: ~10 repetições já criam a antecipação
        # homeostase (s): quanto dura cada reserva
        "energy_span": 300.0,        # acordado e parado, de cheio a vazio
        "sleep_recover": 60.0,       # dormindo, de vazio a cheio
        "stim_decay": 40.0,          # estimulação some sem nada acontecer
        "contact_span": 120.0,       # de satisfeito a carente sem interação
        # memória episódica
        "episode_ok": 45.0,          # objeto que fica isso na tela = aceito
        "episode_window": 15.0,      # janela para ver se a ação teve efeito
        "dismiss_patience": 30.0,    # fechar depois disso já não é tão ruim
        "explore": 0.25,             # chance de testar uma ação qualquer
        # protesto: raiva sustentada vira insatisfação
        "grievance_up": 45.0,        # raiva média de 0,4 chega à revolução em ~3,5 min
        "grievance_down": 420.0,     # ignorado, a insatisfação some em ~7 min
        "stage_up": [0.12, 0.4, 0.68, 1.0],  # reclamação, manifestação, greve, revolução
        "stage_dwell": 20.0,         # s mínimos em cada estágio antes de subir (teste)
        "sad_up": 30.0,              # tristeza: ~30 s de tristeza leva ao abandono (sozinho: ~5 min)
        "sad_down": 300.0,
        "sad_stage_up": [0.2, 0.5, 0.8, 1.0],
        "stage_hyst": 0.06,          # cartaz só some quando cai este tanto abaixo do limiar
    },
    "normal": {
        "mischief_interval": (180.0, 480.0),
        "max_objects": 3,
        "emotion_tau": 5.0,
        "emotion_dwell": 1.5,
        "roam_interval": (6.0, 15.0),
        "drama_window": 15.0,
        "drama_count": 3,
        "away_after": 60.0,
        "righting_after": 8.0,
        "learn_rate": 0.001,
        "cond_rate": 0.03,
        "energy_span": 6 * 3600.0,
        "sleep_recover": 20 * 60.0,
        "stim_decay": 240.0,
        "contact_span": 40 * 60.0,
        "episode_ok": 300.0,
        "episode_window": 30.0,
        "dismiss_patience": 60.0,
        "explore": 0.1,
        "grievance_up": 900.0,       # pavio mais curto (~30 min de provocação até a revolução)
        "grievance_down": 3600.0,
        "stage_up": [0.25, 0.5, 0.75, 1.0],
        "stage_dwell": 75.0,         # s mínimos em cada estágio antes de subir (normal)
        "sad_up": 2400.0,            # tristeza: ~40 min sozinho ou triste leva ao abandono
        "sad_down": 5400.0,
        "sad_stage_up": [0.25, 0.5, 0.75, 1.0],
        "stage_hyst": 0.12,
    },
}


def check_assets(conteudo):
    """Lista o que falta no conteúdo do pet (pets/<pet>/ ou assets/comum/), para avisar em vez de quebrar."""
    warnings = []
    pasta = _relativo(conteudo.proprio)
    if not conteudo.memes.exists():
        warnings.append(f"sem pasta memes/ em {pasta} nem em assets/comum/: sem memes")
    elif not any(list_images(conteudo.memes / e) for e in EMOTIONS):
        warnings.append(f"a pasta {_relativo(conteudo.memes)} está vazia: sem memes")
    if not conteudo.notes.exists():
        warnings.append(f"sem recadinhos.txt em {pasta}: sem post-its")
    if not conteudo.signs.exists():
        warnings.append(f"sem cartazes.txt em {pasta}: usando frases neutras")
    return warnings


def _relativo(caminho):
    """Caminho curto para mensagens: só as duas últimas partes da pasta, com a barra no fim."""
    return "/".join(caminho.parts[-2:]) + "/"


def profile(perms):
    """Tempos do pet para o modo escolhido: 'teste' é acelerado, 'normal' é o real."""
    return PROFILES["teste" if perms.get("modo_teste") else "normal"]


# ============================================================
# PETS
# ============================================================

APP_NOME = "Pestinha"             # o programa; cada personagem tem o próprio nome (pets/<pet>.json)
PET_PADRAO = "mia"

DEFAULT_PET = {
    "nome": None,                       # sem nome no .json: o id com inicial maiúscula
    "seed": 7,
    "brincadeira": {"bola": 1.0, "arremesso": 0.6, "postit": 0.5},   # pesos: 0 desliga
    "temperamento": {},
    "reacao_notebook": "bravo",         # o que sente se arrancarem o notebook: "bravo" ou "triste"
}


def list_pets(paths):
    """Os personagens são os pets/<id>.json com id válido. Pasta de memória não cria personagem."""
    if not paths.pets.exists():
        return [PET_PADRAO]
    names = sorted(p.stem for p in paths.pets.glob("*.json") if pet_id_valido(p.stem))
    return names or [PET_PADRAO]


def escolher_pet(paths, pedido):
    """O pet salvo, se ainda existir; senão o padrão (ou o primeiro que houver)."""
    pets = list_pets(paths)
    if pedido in pets:
        return pedido
    return PET_PADRAO if PET_PADRAO in pets else pets[0]


def _numero_ok(valor, minimo=0.0):
    """Diz se o valor é um número finito e não negativo (ou maior que `minimo`)."""
    return (type(valor) in (int, float) and valor == valor and valor not in (float("inf"),)
            and valor >= minimo)


def _pet_valido(saved):
    """Só os campos do tipo certo entram; o resto fica com o padrão."""
    out = {}
    if isinstance(saved.get("nome"), str) and saved["nome"].strip():
        out["nome"] = saved["nome"]
    if type(saved.get("seed")) is int and saved["seed"] >= 0:
        out["seed"] = saved["seed"]
    brinc = saved.get("brincadeira")
    if isinstance(brinc, dict) and all(isinstance(k, str) and _numero_ok(v) for k, v in brinc.items()):
        out["brincadeira"] = dict(brinc)
    temp = saved.get("temperamento")
    if isinstance(temp, dict) and all(isinstance(k, str) and _numero_ok(v) for k, v in temp.items()):
        out["temperamento"] = dict(temp)
    if saved.get("reacao_notebook") in ("bravo", "triste", "misto"):
        out["reacao_notebook"] = saved["reacao_notebook"]
    if isinstance(saved.get("aparencia"), dict):
        out["aparencia"] = dict(saved["aparencia"])    # cores e acessórios: validados em body/desenho_rosto.py
    return out


def load_pet(paths, name):
    """Carrega o personagem: pets/<pet>.json sobre o padrão, com o nome e o id."""
    pet = dict(DEFAULT_PET)
    saved = read_json(paths.definicao(name), default=None)
    if isinstance(saved, dict):
        pet.update(_pet_valido(saved))
    pet["id"] = name
    if not pet["nome"]:
        pet["nome"] = name.capitalize()
    res_pet = pet
    return res_pet



PERFIS_TEMPERAMENTO = {
    "equilibrado": {"PLAYFUL->CHEER": 1.15, "PEDIDO->SENTAR": 0.75},
    "calmo": {"CALM->CONTENT": 1.35, "PLAYFUL->TRAVESSURA": 0.75, "PEDIDO->SENTAR": 0.9},
    "caotico": {"PLAYFUL->TRAVESSURA": 1.4, "FRUSTRATION->SCOWL": 1.3, "PEDIDO->SENTAR": 0.6},
}


def criar_pet_personalizado(paths, dados):
    """Cria a definição JSON e as pastas iniciais de um novo personagem pelo assistente."""
    import re
    bruto = str((dados or {}).get("id") or (dados or {}).get("nome") or "novo_pet").strip().lower()
    pet_id = re.sub(r"[^a-z0-9_-]+", "_", bruto).strip("_-")[:40] or "novo_pet"
    if not pet_id_valido(pet_id):
        pet_id = "novo_pet"
    nome = str((dados or {}).get("nome") or pet_id.capitalize()).strip() or pet_id.capitalize()
    seed = int((dados or {}).get("seed", 101)) if isinstance((dados or {}).get("seed"), int) else 101
    reacao = (dados or {}).get("reacao_notebook", "misto")
    if reacao not in ("bravo", "triste", "misto"):
        reacao = "misto"
    estilo_temp = (dados or {}).get("estilo_temperamento", "equilibrado")
    temperamento = dict(PERFIS_TEMPERAMENTO.get(estilo_temp, PERFIS_TEMPERAMENTO["equilibrado"]))
    if isinstance((dados or {}).get("temperamento"), dict):
        temperamento.update(_pet_valido({"temperamento": dados["temperamento"]}).get("temperamento", {}))
    aparencia = {
        "formato": str((dados or {}).get("formato", "arredondado")),
        "fundo": str((dados or {}).get("fundo", "#2a1f2d")),
        "borda": str((dados or {}).get("borda", "#ff8da1")),
        "olho": str((dados or {}).get("olho", "#e0115f")),
        "boca": str((dados or {}).get("boca", "#ffebf0")),
        "bochecha": str((dados or {}).get("bochecha", "#ff85a2")),
        "acessorios": list((dados or {}).get("acessorios", ["orelhas_gatinho"])),
    }
    definicao = {
        "nome": nome,
        "seed": max(0, seed),
        "reacao_notebook": reacao,
        "temperamento": temperamento,
        "brincadeira": {"chutar": 0.35, "buscar": 0.30, "atirar": 0.20, "postit": 0.15},
        "aparencia": aparencia,
    }
    write_json(paths.definicao(pet_id), definicao, indent=2)
    conteudo = paths.conteudo(pet_id)
    conteudo.proprio.mkdir(parents=True, exist_ok=True)
    for emocao in list(EMOTIONS) + ["trabalhando"]:
        (conteudo.proprio / "memes" / emocao).mkdir(parents=True, exist_ok=True)
    recados = (dados or {}).get("recadinhos") or [
        f"Oi! Eu sou {nome} e estou de olho nesse código!",
        "Já salvou seu arquivo hoje?",
        "Faz um carinho aqui antes do próximo commit!",
    ]
    tristes = (dados or {}).get("recadinhos_tristes") or [
        f"{nome} ficou no vácuo...",
        "Ninguém brinca comigo hoje...",
    ]
    if not conteudo.notes.exists():
        conteudo.notes.write_text("\n".join(recados) + "\n", encoding="utf-8")
    if not conteudo.notes_sad.exists():
        conteudo.notes_sad.write_text("\n".join(tristes) + "\n", encoding="utf-8")
    if not conteudo.signs.exists():
        conteudo.signs.write_text(
            "[greve_1]\nPRECISO DE ATENÇÃO!\n[greve_2]\nGREVE DE CARINHO!\n"
            "[greve_3]\nPARALISAÇÃO GERAL!\n[revolucao]\nABAIXO O CURSOR!\n"
            "[acordo]\nACORDO FECHADO ♥\n[triste_1]\nESQUECERAM DE MIM...\n"
            "[triste_2]\nABANDONO TOTAL\n[volto]\nVOLTEI ♥\n"
            "[castigo]\nINOCENTE!!\n[xingamento]\n@#$%&*!!\n",
            encoding="utf-8",
        )
    return pet_id



# ============================================================
# ASSETS
# ============================================================


def list_images(folder):
    """Imagens (png, jpg, gif, webp, bmp) de uma pasta; pasta inexistente vira lista vazia."""
    if not folder.exists():
        return []
    return [p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXT]


def meme_for(memes_dir, emotion):
    """Meme da pasta da emoção; se vazia, de qualquer emoção da mesma pasta (do mesmo pet); se nada, None."""
    own = list_images(memes_dir / emotion)
    if own:
        return random.choice(own)
    every = [img for e in EMOTIONS for img in list_images(memes_dir / e)]
    return random.choice(every) if every else None


def random_photo(fotos_dir):
    """Uma foto ao acaso da pasta de fotos, ou None se não houver."""
    photos = list_images(fotos_dir)
    return random.choice(photos) if photos else None


class Notes:
    """Frases de recadinhos.txt (uma por linha, # é comentário). Relê se o arquivo mudar."""

    def __init__(self, path):
        """Post-its de um arquivo de texto (uma frase por linha), relidos quando o arquivo muda."""
        self.path = path
        self.mtime = None
        self.lines = []
        self.last = None

    def _reload(self):
        """Relê o arquivo só se a data de modificação mudou (assim dá para editar com o pet aberto)."""
        try:
            mtime = self.path.stat().st_mtime
        except OSError:
            self.lines = []
            return
        if mtime == self.mtime:
            return
        self.mtime = mtime
        self.lines = [
            line.strip() for line in read_lines(self.path)
            if line.strip() and not line.lstrip().startswith("#")
        ]

    def has_lines(self):
        """Diz se há algum post-it disponível."""
        self._reload()
        return bool(self.lines)

    def pick(self):
        """Um post-it ao acaso, sem repetir o último quando há outros."""
        self._reload()
        if not self.lines:
            return None
        options = [l for l in self.lines if l != self.last] or self.lines
        self.last = random.choice(options)
        return self.last
