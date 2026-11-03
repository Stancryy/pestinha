"""Testes de suporte a múltiplos monitores (3 telas) e escalas de DPI mistas (100%, 125%, 150%)."""

from types import SimpleNamespace
from unittest.mock import Mock

from PySide6.QtWidgets import QApplication

from pestinha import config
from pestinha.paths import Paths
from pestinha.settings_store import SettingsStore


def _criar_app(tmp_path, monkeypatch):
    QApplication.instance() or QApplication([])
    import pestinha.app as app_mod

    monkeypatch.setattr(app_mod, "PanicHotkey", lambda: SimpleNamespace(ok=True, pressed=Mock()))
    paths = Paths(root=tmp_path)
    (paths.pets / "teste").mkdir(parents=True)
    (paths.pets / "teste.json").write_text('{"nome": "Teste", "seed": 7}', encoding="utf-8")
    store = SettingsStore(paths)
    store.update(dict(config.DEFAULT_PERMISSIONS, pet="teste", ativo=True, pousar_janelas=True))
    app = app_mod.PestinhaApp(store, paths)
    for t in app.findChildren(app_mod.QTimer):
        t.stop()
    return app, app_mod


def test_scan_windows_encontra_plataformas_nos_3_monitores_com_dpi_misto(tmp_path, monkeypatch):
    app, app_mod = _criar_app(tmp_path, monkeypatch)
    # 3 monitores: Monitor 1 (0..1920, DPI 1.0), Monitor 2 (1920..3840, DPI 1.25), Monitor 3 (-1920..0, DPI 1.5)
    monitores_info = [
        ((0, 0, 1920, 1080), 1.0),
        ((1920, 0, 3840, 1080), 1.25),
        ((-1920, 0, 0, 1080), 1.5),
    ]
    monkeypatch.setattr(app, "_screens_info", lambda: monitores_info)
    # Janelas em pixels físicos para cada monitor
    janelas_fisicas = [
        (101, (200, 150, 800, 600), False),  # Monitor 1 (1.0x)
        (102, (int(2200 * 1.25), int(200 * 1.25), int(2800 * 1.25), int(700 * 1.25)), False),  # Monitor 2 (1.25x)
        (103, (int(-1400 * 1.5), int(180 * 1.5), int(-800 * 1.5), int(650 * 1.5)), False),  # Monitor 3 (1.5x)
    ]
    monkeypatch.setattr(app_mod.senses, "list_windows", lambda _exc, _dpr: janelas_fisicas)

    app.scan_windows()
    hwnds = {p[0] for p in app.platforms}
    assert hwnds == {101, 102, 103}
    por_id = {p[0]: p for p in app.platforms}
    assert abs(por_id[102][3] - 200.0) < 1.0
    assert abs(por_id[103][3] - 180.0) < 1.0


def test_tela_cheia_em_outro_monitor_nao_esconde_o_pet(tmp_path, monkeypatch):
    app, app_mod = _criar_app(tmp_path, monkeypatch)
    areas = [(0, 0, 1920, 1080), (1920, 0, 3840, 1080), (-1920, 0, 0, 1080)]
    monkeypatch.setattr(app, "screen_bounds", lambda: areas)
    monkeypatch.setattr(app, "screen_geometries", lambda: areas)
    monkeypatch.setattr(app, "_screens_info", lambda: [(a, 1.0) for a in areas])

    # Pet está no Monitor 2 (x = 2500), mas o jogo em tela cheia está no Monitor 1 (0..1920)
    app.pet.body.x = 2500.0
    app.pet.body.y = 500.0
    monkeypatch.setattr(app_mod.senses, "is_fullscreen", lambda: True)
    monkeypatch.setattr(app_mod.senses, "foreground_rect", lambda _dpr: (0, 0, 1920, 1080))

    app.sense()
    assert app.fullscreen is False
    assert app.pet.isVisible()

    # Se o pet for para o Monitor 1 (onde o jogo está em tela cheia), aí sim fica fullscreen=True
    app.pet.body.x = 500.0
    app.sense()
    assert app.fullscreen is True

