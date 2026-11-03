"""Testes da Etapa 11: acessórios sazonais, efeitos sonoros retrô, conquistas e Diário do Pet."""

from datetime import date
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

from pestinha import log as log_module  # noqa: E402
from pestinha.app import PestinhaApp  # noqa: E402
from pestinha.body.desenho_rosto import PADRAO, acessorio_sazonal, aplicar_skin_sazonal  # noqa: E402
from pestinha.core.conquistas import Conquistas  # noqa: E402
from pestinha.paths import Paths  # noqa: E402
from pestinha.settings_store import SettingsStore  # noqa: E402
from pestinha.world.som import SoundFX, gerar_wav_retro  # noqa: E402


def test_acessorios_sazonais_natal_halloween_e_aniversario():
    assert acessorio_sazonal(date(2026, 12, 25))[0] == "gorro_natal"
    assert acessorio_sazonal(date(2026, 10, 31))[0] == "chifrinhos"
    assert acessorio_sazonal(date(2026, 11, 3), aniversario=(11, 3))[0] == "chapeu_festa"
    assert acessorio_sazonal(date(2026, 5, 15)) is None

    ap_natal = aplicar_skin_sazonal(PADRAO, ativo=True, data=date(2026, 12, 24))
    assert any(nome == "gorro_natal" for nome, _ in ap_natal.acessorios)
    ap_desligado = aplicar_skin_sazonal(PADRAO, ativo=False, data=date(2026, 12, 24))
    assert ap_desligado == PADRAO


def test_efeitos_sonoros_wav_em_memoria_e_respeito_ao_nao_perturbe():
    wav = gerar_wav_retro("conquista", volume=50)
    assert wav.startswith(b"RIFF")
    assert len(wav) > 200

    sfx = SoundFX()
    assert sfx.tocar("pulo", ativo=False, volume=50) is False
    assert sfx.tocar("pulo", ativo=True, volume=50, nao_perturbe=True) is False
    assert sfx.tocar("pulo", ativo=True, volume=0, nao_perturbe=False) is False
    assert sfx.tocar("pulo", ativo=True, volume=65, nao_perturbe=False) is True
    assert sfx.ultimo_som[0] == "pulo"
    assert sfx.ultimo_som[1] == 65


def test_conquistas_desbloqueio_persistencia_e_dados_invalidos(tmp_path):
    arq = tmp_path / "achievements.json"
    c = Conquistas(arq)
    novas = c.registrar("carinhos", 1)
    assert [n[0] for n in novas] == ["primeiro_carinho"]
    assert c.registrar("carinhos", 1) == []     # já desbloqueada
    novas_100 = c.registrar("carinhos", 98)
    assert [n[0] for n in novas_100] == ["cem_carinhos"]
    c.save()

    # Recarrega de arquivo válido
    c2 = Conquistas(arq)
    assert c2.contadores["carinhos"] == 100
    assert "cem_carinhos" in c2.desbloqueadas

    # Dados inválidos são descartados sem quebrar
    arq.write_text(
        '{"contadores": {"carinhos": -5, "inexistente": 99, "commits": true}, '
        '"desbloqueadas": {"id_falso": 123, "primeiro_carinho": "texto"}}',
        encoding="utf-8",
    )
    c3 = Conquistas(arq)
    assert c3.contadores["carinhos"] == 0
    assert "id_falso" not in c3.desbloqueadas


def test_diario_do_pet_abre_e_mostra_conquistas_no_app(tmp_path, monkeypatch):
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
        buddy.apply_perms({"efeitos_sonoros": True, "volume_som": 55})
        buddy.menu_caress()
        assert "primeiro_carinho" in buddy.conquistas.desbloqueadas
        assert buddy.som.ultimo_som is not None

        buddy.open_diary()
        assert buddy.diario_dlg is not None
        assert buddy.diario_dlg.isVisible()
        buddy.diario_dlg.close()
    finally:
        buddy.mischief.clear()
        buddy.tray.icon.hide()
        log_module.desligar_arquivo()
