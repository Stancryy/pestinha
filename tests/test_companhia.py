"""Testes da Etapa 10: Pomodoro no notebook, lembretes gentis de água/postura e comemoração de commits Git."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from pestinha import ajustes, config, log as log_module  # noqa: E402
from pestinha.app import PestinhaApp  # noqa: E402
from pestinha.mind.companhia import ultimo_mtime_git  # noqa: E402
from pestinha.paths import Paths  # noqa: E402
from pestinha.settings_store import SettingsStore  # noqa: E402


def test_pomodoro_ciclo_completo_e_deslocamento_na_pausa(tmp_path, monkeypatch):
    app_qt = QApplication.instance() or QApplication([])
    app_qt.setQuitOnLastWindowClosed(False)
    monkeypatch.setattr("pestinha.app.PanicHotkey", lambda: SimpleNamespace(ok=True, pressed=Mock()))
    monkeypatch.setattr("pestinha.app.senses.get_active_app", lambda: "code.exe")
    monkeypatch.setattr("pestinha.app.senses.get_idle_seconds", lambda: 0.0)
    monkeypatch.setattr("pestinha.app.senses.is_fullscreen", lambda: False)
    monkeypatch.setattr("pestinha.app.senses.list_windows", lambda exclude, escala=1.0: [])

    paths = Paths(tmp_path)
    store = SettingsStore(paths)
    buddy = PestinhaApp(store, paths)
    for t in buddy.findChildren(QTimer):
        t.stop()

    try:
        buddy.companhia.iniciar_pomodoro(now=100.0, foco_min=1.0, pausa_min=1.0)
        assert buddy.companhia.pomodoro_fase == "foco"
        assert buddy.mesa.em_pedido is True

        # Deslocar durante pausa do app empurra o prazo
        buddy.companhia.deslocar(30.0)
        buddy.companhia.tick(now=170.0, dt=1.0)
        assert buddy.companhia.pomodoro_fase == "foco"

        # Fim do foco -> entra em pausa sugerida
        buddy.companhia.tick(now=191.0, dt=1.0)
        assert buddy.companhia.pomodoro_fase == "pausa"
        assert buddy.companhia.pomodoros_concluidos == 1
        assert any("foco concluído" in m for m in buddy.companhia.lembretes_enviados)

        # Fim da pausa -> encerra ciclo
        buddy.companhia.tick(now=252.0, dt=1.0)
        assert buddy.companhia.pomodoro_fase is None
    finally:
        buddy.mischief.clear()
        buddy.tray.icon.hide()
        log_module.desligar_arquivo()


def test_lembretes_agua_postura_e_comemorar_commits_git_opt_in(tmp_path, monkeypatch):
    app_qt = QApplication.instance() or QApplication([])
    app_qt.setQuitOnLastWindowClosed(False)
    monkeypatch.setattr("pestinha.app.PanicHotkey", lambda: SimpleNamespace(ok=True, pressed=Mock()))
    monkeypatch.setattr("pestinha.app.senses.get_active_app", lambda: "code.exe")
    monkeypatch.setattr("pestinha.app.senses.get_idle_seconds", lambda: 0.0)
    monkeypatch.setattr("pestinha.app.senses.is_fullscreen", lambda: False)
    monkeypatch.setattr("pestinha.app.senses.list_windows", lambda exclude, escala=1.0: [])

    # Cria repositório git falso apenas com .git/logs/HEAD
    repo = tmp_path / "meu_repo"
    head_log = repo / ".git" / "logs" / "HEAD"
    head_log.parent.mkdir(parents=True)
    head_log.write_bytes(b"\xff\xfe\x00binario_nao_lido")
    os.utime(head_log, (1000.0, 1000.0))

    assert ultimo_mtime_git(tmp_path / "nao_existe") is None
    assert ultimo_mtime_git(repo) == 1000.0

    paths = Paths(tmp_path)
    store = SettingsStore(paths)
    assert config.DEFAULT_PERMISSIONS["lembretes_saude"] is False
    assert config.DEFAULT_PERMISSIONS["comemorar_commits"] is False

    buddy = PestinhaApp(store, paths)
    for t in buddy.findChildren(QTimer):
        t.stop()

    try:
        buddy.activity = "PROGRAMMING"
        buddy.apply_perms({
            "lembretes_saude": True,
            "comemorar_commits": True,
            "git_repo_path": str(repo),
        })
        # Primeira leitura apenas registra o mtime inicial (1000.0), sem comemorar
        buddy.companhia.tick(now=10.0, dt=1.0)
        assert buddy.companhia.commits_comemorados == 0

        # Novo commit atualiza o mtime para 2000.0 -> comemora!
        os.utime(head_log, (2000.0, 2000.0))
        buddy.companhia.tick(now=12.0, dt=1.0)
        assert buddy.companhia.commits_comemorados == 1
        assert any("Commit novo" in m for m in buddy.companhia.lembretes_enviados)

        # Lembretes de água e postura alternam quando o tempo ativo atinge o intervalo
        esperado_s = ajustes.INTERVALO_LEMBRETE_MIN * 60.0
        buddy.companhia.tick(now=20.0, dt=esperado_s + 1.0)
        assert any("golinho d'água" in m for m in buddy.companhia.lembretes_enviados)
        buddy.companhia.tick(now=30.0, dt=esperado_s + 1.0)
        assert any("postura" in m for m in buddy.companhia.lembretes_enviados)
    finally:
        buddy.mischief.clear()
        buddy.tray.icon.hide()
        log_module.desligar_arquivo()

