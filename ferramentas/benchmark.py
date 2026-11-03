"""Benchmark de desempenho do Pestinha: abertura, rede neural, ciclos think/frame, RAM e tamanho de assets."""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import psutil  # noqa: E402
from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from pestinha import log as log_module  # noqa: E402
from pestinha.app import PestinhaApp  # noqa: E402
from pestinha.core.nervous_system import LIFBrain  # noqa: E402
from pestinha.paths import Paths  # noqa: E402
from pestinha.settings_store import SettingsStore  # noqa: E402


class _BenchmarkPaths(Paths):
    """Usa assets/ e pets/ reais do projeto, mas grava memory/ numa pasta temporária isolada."""

    def __init__(self, tmp_memory: Path):
        super().__init__(root=ROOT)
        object.__setattr__(self, "_tmp_memory", tmp_memory)

    @property
    def memory(self):
        return object.__getattribute__(self, "_tmp_memory")


def medir():
    """Executa as medições de tempo de abertura, passo da rede, ciclos do app, RAM e assets."""
    proc = psutil.Process(os.getpid())
    app_qt = QApplication.instance() or QApplication([])

    # 1. Benchmark isolado da rede neural (200 passos de 100 ms = 20 s simulados)
    brain = LIFBrain(seed=7)
    brain.rng = np.random.default_rng(42)
    brain.stimulate({"WORK": 1.0, "TYPING": 0.8, "POKE": 0.5})
    t0 = time.perf_counter()
    for _ in range(200):
        brain.step(100)
    rede_200_ms = (time.perf_counter() - t0) * 1000.0

    # 2. Tempo de abertura do PestinhaApp (com assets reais) e uso de RAM
    with tempfile.TemporaryDirectory() as tmp:
        b_paths = _BenchmarkPaths(Path(tmp) / "memory")
        store = SettingsStore(b_paths)
        t_open0 = time.perf_counter()
        pet_app = PestinhaApp(store, b_paths)
        abertura_ms = (time.perf_counter() - t_open0) * 1000.0

        # 3. 200 ciclos de frame() + 40 ciclos de think()
        t_ciclo0 = time.perf_counter()
        for i in range(200):
            pet_app.frame()
            if i % 5 == 0:
                pet_app.think()
        ciclos_ms = (time.perf_counter() - t_ciclo0) * 1000.0
        ram_mb = proc.memory_info().rss / (1024 * 1024)

        for timer in pet_app.findChildren(QTimer):
            timer.stop()
        if getattr(pet_app, "hotkey", None) is not None and hasattr(pet_app.hotkey, "unregister"):
            pet_app.hotkey.unregister()
        log_module.desligar_arquivo()

    # 4. Tamanho dos assets comuns
    comum_dir = ROOT / "assets" / "comum"
    assets_kb = sum(f.stat().st_size for f in comum_dir.rglob("*") if f.is_file()) / 1024.0

    _ = app_qt
    return {
        "abertura_ms": round(abertura_ms, 2),
        "rede_200_passos_ms": round(rede_200_ms, 2),
        "ciclos_200f_40t_ms": round(ciclos_ms, 2),
        "ram_rss_mb": round(ram_mb, 2),
        "assets_comum_kb": round(assets_kb, 2),
    }


def main():
    dados = medir()
    print(json.dumps(dados, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
