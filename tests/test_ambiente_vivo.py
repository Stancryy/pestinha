"""Testes da Etapa 9: ciclo adaptativo à rotina, reação opt-in a CPU/RAM e música, e barra de tarefas."""

import csv
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

from pestinha import config, log as log_module  # noqa: E402
from pestinha.app import PestinhaApp  # noqa: E402
from pestinha.paths import Paths  # noqa: E402
from pestinha.sense.timeline import COLUMNS, fator_ciclo_rotina  # noqa: E402
from pestinha.settings_store import SettingsStore  # noqa: E402


def test_ciclo_rotina_adapta_aos_horarios_aprendidos_inclusive_madrugada(tmp_path):
    csv_path = tmp_path / "timeline.csv"
    # Sem arquivo ou com poucas linhas -> neutro (1.0)
    assert fator_ciclo_rotina(csv_path, hora_atual=3) == 1.0

    # Simula usuário que programa de madrugada (3h) e descansa às 10h da manhã
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for i in range(12):
            w.writerow(["2026-11-03T03:00", 1, 3 * 60 + i, "PROGRAMMING", 0.0, 0.0, 0.8, 1, 30.0, 1.0, "feliz"])
        for i in range(12):
            w.writerow(["2026-11-03T10:00", 1, 10 * 60 + i, "AWAY", 1.0, 1.0, 0.0, 0, 0.0, 0.0, "dormindo"])
        # Linha inválida/corrompida no meio não quebra a leitura
        w.writerow(["corrompido", "abc", "nao_int", "IDLE", "x"])

    assert fator_ciclo_rotina(csv_path, hora_atual=3) == 1.15
    assert fator_ciclo_rotina(csv_path, hora_atual=10) == 0.72


def test_reacao_hardware_musica_opt_in_e_barra_de_tarefas(tmp_path, monkeypatch):
    app_qt = QApplication.instance() or QApplication([])
    app_qt.setQuitOnLastWindowClosed(False)
    monkeypatch.setattr("pestinha.app.PanicHotkey", lambda: SimpleNamespace(ok=True, pressed=Mock()))
    monkeypatch.setattr("pestinha.app.senses.get_active_app", lambda: "code.exe")
    monkeypatch.setattr("pestinha.app.senses.get_idle_seconds", lambda: 0.0)
    monkeypatch.setattr("pestinha.app.senses.is_fullscreen", lambda: False)
    monkeypatch.setattr("pestinha.app.senses.list_windows", lambda exclude, escala=1.0: [])
    monkeypatch.setattr("pestinha.app.senses.get_hardware_usage", lambda: (95.0, 92.0))
    monkeypatch.setattr("pestinha.app.senses.is_media_playing", lambda _app="": True)

    paths = Paths(tmp_path)
    store = SettingsStore(paths)
    # Por padrão, reagir_hardware e reagir_musica vêm desligados (opt-in)
    assert config.DEFAULT_PERMISSIONS["reagir_hardware"] is False
    assert config.DEFAULT_PERMISSIONS["reagir_musica"] is False

    buddy = PestinhaApp(store, paths)
    for t in buddy.findChildren(QTimer):
        t.stop()

    try:
        buddy.sense()
        assert buddy.pet_state.suando is False
        assert buddy.pet_state.apertado is False
        assert buddy.pet_state.dancando is False

        # Liga as opções opt-in
        buddy.apply_perms({"reagir_hardware": True, "reagir_musica": True})
        buddy.sense()
        assert buddy.pet_state.suando is True
        assert buddy.pet_state.apertado is True
        assert buddy.pet_state.dancando is True

        buddy.think()
        assert buddy.intensities["SOUND"] >= 0.75
        buddy.pet.repaint()

        # Barra de tarefas como plataforma quando há área reservada pelo sistema
        monkeypatch.setattr(buddy, "screen_bounds", lambda: [(0, 0, 1920, 1040)])
        monkeypatch.setattr(buddy, "screen_geometries", lambda: [(0, 0, 1920, 1080)])
        barras = buddy.plataformas_barra_tarefas()
        assert barras == [("taskbar_0", 10, 1910, 1040)]
    finally:
        buddy.mischief.clear()
        buddy.tray.icon.hide()
        log_module.desligar_arquivo()

