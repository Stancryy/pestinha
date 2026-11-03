"""Regressões encontradas na auditoria: recados gentis, som no Windows e leitura da rotina."""

import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402
from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from pestinha import log as log_module  # noqa: E402
from pestinha.paths import Paths  # noqa: E402
from pestinha.settings_store import SettingsStore  # noqa: E402
from pestinha.world.mischief import MischiefEngine  # noqa: E402
from pestinha.world import som  # noqa: E402


def test_recado_gentil_aparece_e_fechar_nao_vira_castigo(tmp_path):
    QApplication.instance() or QApplication([])
    engine = MischiefEngine(Paths(root=tmp_path).conteudo("mia"))
    dispensas = []
    engine.dismissed.connect(lambda thing, s: dispensas.append(thing))
    try:
        nota = engine.spawn_note(300, 200, "Pausa concluída!", 1000)
        assert nota is not None and nota in engine.things and nota.resting
        engine._on_click(nota)
        assert nota not in engine.things
        assert dispensas == []                       # recado gentil não ensina o pet a ficar triste
        assert engine.spawn_note(10, 10, "", 1000) is None
    finally:
        engine.clear()


def test_lembrete_da_companhia_chega_na_tela(tmp_path, monkeypatch):
    app_qt = QApplication.instance() or QApplication([])
    app_qt.setQuitOnLastWindowClosed(False)
    monkeypatch.setattr("pestinha.app.PanicHotkey", lambda *a: SimpleNamespace(ok=True, pressed=Mock()))
    monkeypatch.setattr("pestinha.app.senses.get_active_app", lambda: "code.exe")
    monkeypatch.setattr("pestinha.app.senses.get_idle_seconds", lambda: 0.0)
    monkeypatch.setattr("pestinha.app.senses.is_fullscreen", lambda: False)
    monkeypatch.setattr("pestinha.app.senses.list_windows", lambda exclude, escala=1.0: [])
    paths = Paths(tmp_path)
    buddy = __import__("pestinha.app", fromlist=["PestinhaApp"]).PestinhaApp(SettingsStore(paths), paths)
    for t in buddy.findChildren(QTimer):
        t.stop()
    try:
        buddy.pet.setVisible(True)
        antes = len(buddy.mischief.things)
        buddy.companhia._entregar_recado_gentil("💧 Um golinho d'água?")
        assert len(buddy.mischief.things) == antes + 1
    finally:
        buddy.mischief.clear()
        buddy.tray.icon.hide()
        log_module.desligar_arquivo()


@pytest.mark.skipif(sys.platform != "win32", reason="API Win32 específica do Windows")
def test_janela_maximizada_com_barra_oculta_nao_e_tela_cheia(monkeypatch):
    from pestinha.plataforma import windows as w
    monkeypatch.setattr(w.win32gui, "GetForegroundWindow", lambda: 1001)
    monkeypatch.setattr(w.win32gui, "GetClassName", lambda hwnd: "Chrome_WidgetWin_1")
    monkeypatch.setattr(w, "_frame_rect", lambda hwnd: (0, 0, 1920, 1080))
    monkeypatch.setattr(w.win32api, "MonitorFromWindow", lambda hwnd, flag: 1)
    monkeypatch.setattr(w.win32api, "GetMonitorInfo", lambda mon: {"Monitor": (0, 0, 1920, 1080)})

    # 1. Janela maximizada (IsZoomed=1) em monitor com barra de tarefas auto-oculta -> NÃO é tela cheia
    monkeypatch.setattr(w.ctypes.windll.user32, "IsZoomed", lambda hwnd: 1)
    monkeypatch.setattr(w.win32gui, "GetWindowLong", lambda hwnd, idx: w.win32con.WS_CAPTION)
    assert w.tela_cheia() is False

    # 2. Menu Iniciar / Pesquisa do Windows 11 (CoreWindow cobrindo 1920x1080) -> NÃO é tela cheia
    monkeypatch.setattr(w.ctypes.windll.user32, "IsZoomed", lambda hwnd: 0)
    monkeypatch.setattr(w.win32gui, "GetWindowLong", lambda hwnd, idx: 0)
    monkeypatch.setattr(w.win32gui, "GetClassName", lambda hwnd: "Windows.UI.Core.CoreWindow")
    assert w.tela_cheia() is False

    # 3. Jogo ou vídeo realmente em tela cheia (sem IsZoomed e sem WS_CAPTION, cobrindo o monitor) -> É tela cheia
    monkeypatch.setattr(w.win32gui, "GetClassName", lambda hwnd: "UnrealWindow")
    assert w.tela_cheia() is True


@pytest.mark.skipif(sys.platform != "win32", reason="winsound só existe no Windows")
def test_som_no_windows_nao_usa_async_com_memoria(monkeypatch):
    import winsound
    chamadas = []
    monkeypatch.setattr(winsound, "PlaySound", lambda dados, flags: chamadas.append(flags))
    monkeypatch.setenv("QT_QPA_PLATFORM", "windows")
    assert som.SoundFX().tocar("pulo", ativo=True, volume=30) is True
    for _ in range(50):
        if chamadas:
            break
        time.sleep(0.02)
    assert chamadas, "o som não foi tocado"
    assert not (chamadas[0] & winsound.SND_ASYNC)    # SND_ASYNC + SND_MEMORY dá RuntimeError no Windows
    assert chamadas[0] & winsound.SND_MEMORY


def test_rotina_nao_e_relida_a_cada_leitura_dos_sentidos(tmp_path, monkeypatch):
    app_qt = QApplication.instance() or QApplication([])
    app_qt.setQuitOnLastWindowClosed(False)
    import pestinha.app as app_mod
    leituras = []
    monkeypatch.setattr(app_mod, "PanicHotkey", lambda *a: SimpleNamespace(ok=True, pressed=Mock()))
    monkeypatch.setattr(app_mod, "fator_ciclo_rotina", lambda path: leituras.append(path) or 1.0)
    monkeypatch.setattr("pestinha.app.senses.get_active_app", lambda: "code.exe")
    monkeypatch.setattr("pestinha.app.senses.get_idle_seconds", lambda: 0.0)
    monkeypatch.setattr("pestinha.app.senses.is_fullscreen", lambda: False)
    monkeypatch.setattr("pestinha.app.senses.list_windows", lambda exclude, escala=1.0: [])
    paths = Paths(tmp_path)
    buddy = app_mod.PestinhaApp(SettingsStore(paths), paths)
    for t in buddy.findChildren(QTimer):
        t.stop()
    try:
        for _ in range(20):
            buddy.sense()
        assert len(leituras) == 1                    # 1 leitura no início; as próximas só depois de 10 min
    finally:
        buddy.mischief.clear()
        buddy.tray.icon.hide()
        log_module.desligar_arquivo()


@pytest.mark.skipif(sys.platform != "win32", reason="API Win32 específica do Windows")
def test_janela_maximizada_com_barra_oculta_nao_e_tela_cheia(monkeypatch):
    from pestinha.plataforma import windows as w
    monkeypatch.setattr(w.win32gui, "GetForegroundWindow", lambda: 1001)
    monkeypatch.setattr(w.win32gui, "GetClassName", lambda hwnd: "Chrome_WidgetWin_1")
    monkeypatch.setattr(w, "_frame_rect", lambda hwnd: (0, 0, 1920, 1080))
    monkeypatch.setattr(w.win32api, "MonitorFromWindow", lambda hwnd, flag: 1)
    monkeypatch.setattr(w.win32api, "GetMonitorInfo", lambda mon: {"Monitor": (0, 0, 1920, 1080)})

    # 1. Janela maximizada (IsZoomed=1) em monitor com barra de tarefas auto-oculta -> NÃO é tela cheia
    monkeypatch.setattr(w.ctypes.windll.user32, "IsZoomed", lambda hwnd: 1)
    monkeypatch.setattr(w.win32gui, "GetWindowLong", lambda hwnd, idx: w.win32con.WS_CAPTION)
    assert w.tela_cheia() is False

    # 2. Menu Iniciar / Pesquisa do Windows 11 (CoreWindow cobrindo 1920x1080) -> NÃO é tela cheia
    monkeypatch.setattr(w.ctypes.windll.user32, "IsZoomed", lambda hwnd: 0)
    monkeypatch.setattr(w.win32gui, "GetWindowLong", lambda hwnd, idx: 0)
    monkeypatch.setattr(w.win32gui, "GetClassName", lambda hwnd: "Windows.UI.Core.CoreWindow")
    assert w.tela_cheia() is False

    # 3. Jogo ou vídeo realmente em tela cheia (sem IsZoomed e sem WS_CAPTION, cobrindo o monitor) -> É tela cheia
    monkeypatch.setattr(w.win32gui, "GetClassName", lambda hwnd: "UnrealWindow")
    assert w.tela_cheia() is True

