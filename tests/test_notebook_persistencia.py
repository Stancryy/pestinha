"""
Valida a persistência do estado escondido do notebook e garante que o pet
nunca senta nem torna o notebook visível quando o usuário abriu um app de trabalho.
"""

from unittest.mock import patch
import pytest
from PySide6.QtWidgets import QApplication

from pestinha.paths import Paths
from pestinha.settings_store import SettingsStore
from pestinha.app import PestinhaApp
from pestinha.sense import senses


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def test_notebook_escondido_persiste_e_bloqueia_trabalho(qapp, tmp_path):
    paths = Paths(root=tmp_path)
    store = SettingsStore(paths)
    app = PestinhaApp(store, paths)

    # Inicialmente o notebook está visível
    assert app.mesa.escondido is False
    assert app.perms.get("notebook_escondido") is False

    # 1. Usuário esconde o notebook pelo menu
    app.menu_alternar_notebook()
    assert app.mesa.escondido is True
    assert app.perms.get("notebook_escondido") is True

    # 2. Ao criar uma nova instância (simulando reabertura do pet), continua escondido
    store2 = SettingsStore(paths)
    assert store2.perms.get("notebook_escondido") is True
    app2 = PestinhaApp(store2, paths)
    assert app2.mesa.escondido is True
    assert app2.mesa.caderno.isHidden() is True

    # 3. Usuário abre app de trabalho (ex: VS Code)
    with patch.object(senses, "get_active_app", return_value="code"), \
         patch.object(senses, "get_idle_seconds", return_value=0.0):
        for _ in range(30):
            app2.sense()
            app2.think()
            app2.frame()

    # O pet NUNCA senta no notebook escondido e o notebook NUNCA fica visível
    assert app2.activity == "PROGRAMMING"
    assert app2.mesa.escondido is True
    assert app2.mesa.sentado is False
    assert app2.pet_state.at_desk is False
    assert app2.mesa.caderno.isHidden() is True

    # Limpeza
    app.mesa.fechar()
    app2.mesa.fechar()
    app.pet.close()
    app2.pet.close()
