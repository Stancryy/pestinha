"""Testes da Etapa 7: trava de instância única, atalhos configuráveis, iniciar com o Windows e modo Não Perturbe."""

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

from pestinha import config, log as log_module, plataforma  # noqa: E402
from pestinha.app import PestinhaApp  # noqa: E402
from pestinha.paths import Paths  # noqa: E402
from pestinha.settings_store import SettingsStore  # noqa: E402


def test_trava_instancia_unica_bloqueia_pid_vivo_e_recupera_pid_morto(tmp_path):
    lock = tmp_path / "pestinha.lock"
    assert plataforma.adquirir_trava_instancia(lock, meu_pid=100, pid_ativo_fn=lambda pid: pid == 100) is True
    # Outra instância (PID 200) vê que o PID 100 ainda está ativo: bloqueia
    assert plataforma.adquirir_trava_instancia(lock, meu_pid=200, pid_ativo_fn=lambda pid: pid == 100) is False
    # Se o PID 100 morreu, o PID 200 assume a trava
    assert plataforma.adquirir_trava_instancia(lock, meu_pid=200, pid_ativo_fn=lambda _pid: False) is True
    assert lock.read_text(encoding="utf-8").strip() == "200"

    # Arquivo corrompido não impede de abrir
    lock.write_text("nao-eh-numero", encoding="utf-8")
    assert plataforma.adquirir_trava_instancia(lock, meu_pid=300, pid_ativo_fn=lambda _pid: True) is True

    # Liberar só apaga se for do mesmo PID
    plataforma.liberar_trava_instancia(lock, meu_pid=999)
    assert lock.exists()
    plataforma.liberar_trava_instancia(lock, meu_pid=300)
    assert not lock.exists()


def test_atalho_inicializar_windows_cria_e_remove_em_pasta_isolada(tmp_path):
    assert plataforma.iniciar_com_windows_ativo(tmp_path) is False
    assert plataforma.configurar_iniciar_com_windows(True, tmp_path) is True
    assert plataforma.iniciar_com_windows_ativo(tmp_path) is True
    conteudo = plataforma.caminho_atalho_inicializar(tmp_path).read_text(encoding="utf-8")
    assert "--direto" in conteudo
    assert plataforma.configurar_iniciar_com_windows(False, tmp_path) is True
    assert plataforma.iniciar_com_windows_ativo(tmp_path) is False


def test_parse_e_formatacao_de_atalhos_com_fallback_para_dados_invalidos():
    mods, tecla = plataforma.parse_atalho("ctrl + shift + f9")
    assert mods == {"CTRL", "SHIFT"}
    assert tecla == "F9"
    assert plataforma.formatar_atalho("shift+ctrl+p") == "Ctrl + Shift + P"

    # Dados inválidos voltam para o padrão Ctrl + Alt + Shift + B
    mods_inv, tecla_inv = plataforma.parse_atalho("atalho_invalido_sem_modificador")
    assert mods_inv == {"CTRL", "ALT", "SHIFT"}
    assert tecla_inv == "B"
    assert plataforma.formatar_atalho(None) == "Ctrl + Alt + Shift + B"


def test_modo_nao_perturbe_automatico_em_jogo_e_reuniao(tmp_path, monkeypatch):
    app_qt = QApplication.instance() or QApplication([])
    app_qt.setQuitOnLastWindowClosed(False)
    monkeypatch.setattr("pestinha.app.PanicHotkey", lambda: SimpleNamespace(ok=True, pressed=Mock()))
    monkeypatch.setattr("pestinha.app.senses.get_active_app", lambda: "code.exe")
    monkeypatch.setattr("pestinha.app.senses.get_idle_seconds", lambda: 0.0)
    monkeypatch.setattr("pestinha.app.senses.is_fullscreen", lambda: False)
    monkeypatch.setattr("pestinha.app.senses.list_windows", lambda exclude, escala=1.0: [])

    paths = Paths(tmp_path)
    store = SettingsStore(paths)
    store.update(dict(config.DEFAULT_PERMISSIONS, rotina=False, travessuras=True, bolinha=True, nao_perturbe_auto=True))
    buddy = PestinhaApp(store, paths)
    for t in buddy.findChildren(QTimer):
        t.stop()

    try:
        assert buddy.em_nao_perturbe is False
        assert buddy.ball.isVisible() is True

        # Entrou em jogo (GAMING): ativa Não Perturbe e esconde a bolinha
        monkeypatch.setattr("pestinha.app.senses.get_active_app", lambda: "valorant.exe")
        buddy.sense()
        assert buddy.activity == "GAMING"
        assert buddy.em_nao_perturbe is True
        assert buddy.ball.isVisible() is False

        # Voltou a programar, mas entrou em reunião (Zoom): continua em Não Perturbe
        monkeypatch.setattr("pestinha.app.senses.get_active_app", lambda: "zoom.exe")
        buddy.sense()
        assert buddy.em_nao_perturbe is True

        # Voltou para o VS Code: sai do Não Perturbe e devolve a bolinha
        monkeypatch.setattr("pestinha.app.senses.get_active_app", lambda: "code.exe")
        buddy.sense()
        assert buddy.em_nao_perturbe is False
        assert buddy.ball.isVisible() is True

        # Alternância manual pela bandeja
        buddy.toggle_dnd()
        assert buddy.em_nao_perturbe is True
        buddy.toggle_dnd()
        assert buddy.em_nao_perturbe is False
    finally:
        buddy.mischief.clear()
        buddy.tray.icon.hide()
        log_module.desligar_arquivo()
