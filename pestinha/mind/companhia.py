"""
COMPANHIA - funções de companhia para quem programa: Pomodoro no notebook,
lembretes gentis de água/postura e comemoração de commits locais do Git.

Regras de privacidade e respeito:
- Lembretes e comemoração de commits vêm desligados por padrão (opt-in).
- O detector de commit olha APENAS a data de modificação (`st_mtime`) de
  `.git/logs/HEAD` ou `.git/HEAD`, sem nunca abrir nem ler o conteúdo.
- Todas as mensagens têm tom leve e positivo, sem culpar nem pressionar.
"""

from pathlib import Path

from .. import ajustes


def ultimo_mtime_git(repo_path):
    """
    Devolve o maior `st_mtime` entre `.git/logs/HEAD` e `.git/HEAD` da pasta `repo_path`,
    ou None se não for um repositório Git. Nunca lê o conteúdo dos arquivos.
    """
    if not repo_path:
        return None
    try:
        base = Path(repo_path)
    except (TypeError, ValueError):
        return None
    git_dir = base / ".git"
    mtimes = []
    for rel in (("logs", "HEAD"), ("HEAD",)):
        alvo = git_dir.joinpath(*rel)
        try:
            if alvo.exists():
                mtimes.append(float(alvo.stat().st_mtime))
        except OSError:
            continue
    return max(mtimes) if mtimes else None


class CompanhiaController:
    """Controla o ciclo de Pomodoro, os lembretes opcionais de saúde e a comemoração de commits Git."""

    def __init__(self, app):
        """Inicializa os contadores da sessão sem disparar notificações no arranque."""
        self.app = app
        self.pomodoro_fase = None       # None, "foco" ou "pausa"
        self.pomodoro_fim = 0.0
        self.pausa_s = 300.0
        self.pomodoros_concluidos = 0

        self.tempo_ativo_lembrete = 0.0
        self._alterna_lembrete = False
        self.lembretes_enviados = []

        self._git_mtime = None
        self._git_repo_observado = None
        self._ultimo_check_git = -1e9
        self.commits_comemorados = 0

    def iniciar_pomodoro(self, now, foco_min=None, pausa_min=None):
        """Começa um ciclo de foco junto com o pet no notebook."""
        f_min = ajustes.POMODORO_FOCO_MIN if foco_min is None else max(0.05, float(foco_min))
        p_min = ajustes.POMODORO_PAUSA_MIN if pausa_min is None else max(0.05, float(pausa_min))
        self.pomodoro_fase = "foco"
        self.pomodoro_fim = now + f_min * 60.0
        self.pausa_s = p_min * 60.0
        self.app.mesa.pedir(now)

    def parar_pomodoro(self):
        """Cancela o ciclo de Pomodoro em andamento."""
        self.pomodoro_fase = None
        self.pomodoro_fim = 0.0

    def deslocar(self, segundos):
        """Empurra o prazo do Pomodoro durante a pausa do app."""
        if self.pomodoro_fase is not None:
            self.pomodoro_fim += segundos

    def _entregar_recado_gentil(self, texto):
        """Mostra um post-it leve perto do pet (se visível e fora do modo Não Perturbe)."""
        self.lembretes_enviados.append(texto)
        if not self.app.pet.isVisible() or self.app.em_nao_perturbe:
            return
        try:
            chao = int(self.app.bounds()[3])
            x = int(self.app.pet.body.x - 90)
            y = int(max(40, self.app.pet.body.y - 110))
            self.app.mischief.spawn_note(x, y, texto, chao)
        except Exception:
            pass

    def tick(self, now, dt):
        """Atualiza Pomodoro, lembretes de água/postura e verificação de commit Git."""
        # 1. Pomodoro
        if self.pomodoro_fase == "foco":
            self.app.mesa.pedido_ate = max(self.app.mesa.pedido_ate, now + 5.0)
            self.app.mesa.em_pedido = not self.app.mesa.sentado
            if now >= self.pomodoro_fim:
                self.pomodoros_concluidos += 1
                if hasattr(self.app, "registrar_conquista"):
                    self.app.registrar_conquista("pomodoros", 1)
                self.pomodoro_fase = "pausa"
                self.pomodoro_fim = now + self.pausa_s
                minutos_pausa = max(1, int(round(self.pausa_s / 60.0)))
                self._entregar_recado_gentil(
                    f"🎉 Ciclo de foco concluído! Que tal uma pausa leve de {minutos_pausa} min? ☕"
                )
        elif self.pomodoro_fase == "pausa" and now >= self.pomodoro_fim:
            self.pomodoro_fase = None
            self._entregar_recado_gentil("✨ Pausa concluída! Quando quiser, estamos prontos.")

        # 2. Lembretes opcionais de água e postura
        if (
            self.app.perms.get("lembretes_saude", False)
            and self.app.activity != "AWAY"
            and not self.app.asleep
            and not self.app.em_nao_perturbe
        ):
            self.tempo_ativo_lembrete += dt
            if self.tempo_ativo_lembrete >= ajustes.INTERVALO_LEMBRETE_MIN * 60.0:
                self.tempo_ativo_lembrete = 0.0
                self._alterna_lembrete = not self._alterna_lembrete
                msg = (
                    "💧 Hidratação amiga: que tal um golinho d'água quando puder?"
                    if self._alterna_lembrete
                    else "✨ Pausa rápida pros ombros: relaxa a postura um pouquinho!"
                )
                self._entregar_recado_gentil(msg)

        # 3. Comemorar commits do Git (só olha st_mtime, nunca lê o arquivo)
        if self.app.perms.get("comemorar_commits", False) and now - self._ultimo_check_git >= 1.0:
            self._ultimo_check_git = now
            repo_cfg = (self.app.perms.get("git_repo_path") or "").strip()
            repo = Path(repo_cfg) if repo_cfg else self.app.paths.root
            mtime = ultimo_mtime_git(repo)
            if repo != self._git_repo_observado:
                self._git_repo_observado = repo
                self._git_mtime = mtime
            elif mtime is not None:
                if self._git_mtime is None:
                    self._git_mtime = mtime
                elif mtime > self._git_mtime:
                    self._git_mtime = mtime
                    self.commits_comemorados += 1
                    if hasattr(self.app, "registrar_conquista"):
                        self.app.registrar_conquista("commits", 1)
                    if not self.app.asleep:
                        self.app.emotion.force("feliz", 2.5, now, 90)
                    if self.app._pode_soltar_fogo():
                        self.app.festa.fogos.launch(int(self.app.pet.body.x), int(self.app.pet.body.y - 60))
                    self._entregar_recado_gentil("🚀 Commit novo detectado! Mandou muito bem!")
