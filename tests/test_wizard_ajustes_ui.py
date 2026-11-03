"""Testes da Etapa 8: tela de Ajustes Finos (`ajustes.py`), Editor de Programas e Wizard de Personagem."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from pestinha import ajustes, config  # noqa: E402
from pestinha.paths import Paths  # noqa: E402
from pestinha.sense import senses  # noqa: E402
from pestinha.ui.ferramentas_ui import AjustesDialog, AtividadesDialog, WizardPetDialog  # noqa: E402


def _garantir_qapp():
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def test_ajustes_persistencia_limites_e_dados_invalidos(tmp_path):
    paths = Paths(root=tmp_path)
    try:
        # Valores fora de _LIMITES são limitados ao intervalo válido; tipos inválidos são ignorados
        novos = ajustes.salvar_ajustes(paths.ajustes, {
            "GRAVIDADE": 3000.0,
            "INTERVALO_QUADRO_ATIVO_MS": 2,      # abaixo do mínimo 8 -> vira 8
            "QUICA": 99.0,                       # acima do máximo 1.0 -> vira 1.0
            "TROCAS_CARINHO": True,              # bool é ignorado
            "TAMANHO_MEME": "invalido",          # texto é ignorado
            "CHAVE_INEXISTENTE": 123,
        })
        assert novos["GRAVIDADE"] == 3000.0
        assert novos["INTERVALO_QUADRO_ATIVO_MS"] == 8
        assert novos["QUICA"] == 1.0
        assert ajustes.GRAVIDADE == 3000.0

        # JSON corrompido não derruba o carregamento
        paths.ajustes.write_text("{json_quebrado", encoding="utf-8")
        atuais = ajustes.carregar_ajustes(paths.ajustes)
        assert isinstance(atuais, dict)
    finally:
        ajustes.restaurar_padroes(paths.ajustes)
    assert ajustes.GRAVIDADE == ajustes.VALORES_PADRAO["GRAVIDADE"]
    assert not paths.ajustes.exists()


def test_dialogo_ajustes_filtra_salva_e_restaura(tmp_path):
    _garantir_qapp()
    paths = Paths(root=tmp_path)
    try:
        dlg = AjustesDialog(paths)
        dlg._filtrar("GRAVIDADE")
        assert dlg.linhas["GRAVIDADE"][0].isHidden() is False
        assert dlg.linhas["QUICA"][0].isHidden() is True

        dlg.campos["GRAVIDADE"].setValue(2500.0)
        dlg._salvar()
        assert paths.ajustes.exists()
        assert ajustes.GRAVIDADE == 2500.0

        dlg._restaurar()
        assert ajustes.GRAVIDADE == ajustes.VALORES_PADRAO["GRAVIDADE"]
    finally:
        ajustes.restaurar_padroes(paths.ajustes)


def test_dialogo_atividades_adiciona_categoria_e_salva(tmp_path):
    _garantir_qapp()
    paths = Paths(root=tmp_path)
    try:
        dlg = AtividadesDialog(paths)
        dlg.nova_cat_edit.setText("studying")
        dlg._criar_categoria()
        assert "STUDYING" in dlg.editores
        dlg.editores["STUDYING"].setPlainText("anki.exe, zotero")
        dlg._salvar()
        assert paths.activities.exists()
        assert senses.detect_activity("anki.exe", 0.0, 300.0) == "STUDYING"
    finally:
        senses.ACTIVITY_APPS = {k: list(v) for k, v in senses.DEFAULT_ACTIVITY_APPS.items()}


def test_wizard_cria_personagem_completo_e_higieniza_id_invalido(tmp_path):
    _garantir_qapp()
    paths = Paths(root=tmp_path)
    wiz = WizardPetDialog(paths)
    wiz.nome_edit.setText("Luna")
    wiz.id_edit.setText("../Luna Pet!!")
    wiz.temp_combo.setCurrentIndex(2)  # caotico
    criados = []
    wiz.pet_criado.connect(criados.append)
    wiz._criar()

    assert criados == ["luna_pet"]
    pet = config.load_pet(paths, "luna_pet")
    assert pet["nome"] == "Luna"
    assert pet["reacao_notebook"] == "misto"
    conteudo = paths.conteudo("luna_pet")
    assert conteudo.notes.exists()
    assert conteudo.notes_sad.exists()
    assert conteudo.signs.exists()
    assert (conteudo.memes / "feliz").is_dir()
