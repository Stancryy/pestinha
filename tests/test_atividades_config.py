"""Testes para ACTIVITY_APPS configurável em JSON, programas do usuário e reação mista no notebook."""

from types import SimpleNamespace
from unittest.mock import Mock

from PySide6.QtWidgets import QApplication

from pestinha import config
from pestinha.paths import Paths
from pestinha.sense import senses
from pestinha.settings_store import SettingsStore


def test_programas_do_usuario_estao_nas_categorias_certas():
    senses.carregar_atividades(None)
    assert senses.detect_activity("Antigravity IDE.exe", 0.0, 60.0) == "PROGRAMMING"
    assert senses.detect_activity("agy.exe", 0.0, 60.0) == "PROGRAMMING"
    assert senses.detect_activity("cursor.exe", 0.0, 60.0) == "PROGRAMMING"
    assert senses.detect_activity("trae.exe", 0.0, 60.0) == "PROGRAMMING"
    assert senses.detect_activity("LM Studio.exe", 0.0, 60.0) == "PROGRAMMING"
    assert senses.detect_activity("powershell.exe", 0.0, 60.0) == "PROGRAMMING"
    assert senses.detect_activity("comfyui.exe", 0.0, 60.0) == "DESIGNING"
    assert senses.detect_activity("capcut.exe", 0.0, 60.0) == "DESIGNING"
    assert senses.detect_activity("RobloxPlayerBeta.exe", 0.0, 60.0) == "GAMING"
    assert senses.detect_activity("RobloxStudioBeta.exe", 0.0, 60.0) == "GAMING"
    assert senses.detect_activity("construct3.exe", 0.0, 60.0) == "GAMING"


def test_salvar_e_carregar_activities_json(tmp_path):
    p = Paths(root=tmp_path)
    senses.salvar_atividades(p.activities, {"PROGRAMMING": ["MeuEditor.exe", "  agy  "]})
    assert p.activities.exists()
    assert senses.detect_activity("meueditor.exe", 0.0, 60.0) == "PROGRAMMING"
    senses.carregar_atividades(None)


def test_activities_json_invalido_usa_padrao_sem_quebrar(tmp_path):
    p = Paths(root=tmp_path)
    p.memory.mkdir(parents=True)
    p.activities.write_text('{"PROGRAMMING": "nao_e_lista", "GAMING": [123, null, ""]}', encoding="utf-8")
    carregado = senses.carregar_atividades(p.activities)
    assert "antigravity" in carregado["PROGRAMMING"]
    assert "robloxplayerbeta" in carregado["GAMING"]


def test_reacao_notebook_misto_alterna_entre_bravo_e_triste(tmp_path, monkeypatch):
    QApplication.instance() or QApplication([])
    import pestinha.app as app_mod

    monkeypatch.setattr(app_mod, "PanicHotkey", lambda: SimpleNamespace(ok=True, pressed=Mock()))
    paths = Paths(root=tmp_path)
    (paths.pets / "teste").mkdir(parents=True)
    (paths.pets / "teste.json").write_text(
        '{"nome": "Teste", "seed": 7, "reacao_notebook": "misto"}', encoding="utf-8"
    )
    store = SettingsStore(paths)
    store.update(dict(config.DEFAULT_PERMISSIONS, pet="teste", ativo=True))
    app = app_mod.PestinhaApp(store, paths)
    for t in app.findChildren(app_mod.QTimer):
        t.stop()

    assert app.reacao_notebook == "misto"
    raiva0 = app.protest.grievance
    triste0 = app.sad.grievance
    app.arrancar_notebook(10.0)
    app.arrancar_notebook(20.0)
    assert app.protest.grievance > raiva0
    assert app.sad.grievance > triste0

