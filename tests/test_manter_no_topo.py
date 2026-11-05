"""
Testes de garantia de z-order (manter_no_topo) para que o pet nunca fique
atrás de janelas do navegador ou de aplicativos quando novas abas/janelas abrem.
"""

from unittest.mock import MagicMock, patch
import pytest
from PySide6.QtWidgets import QApplication

from pestinha import plataforma
from pestinha.body.pet import PetWindow
from pestinha.body.pet_state import PetState


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def test_garantir_topo_funciona_sem_erro(qapp):
    """Valida que plataforma.garantir_topo pode ser chamado em qualquer sistema sem exceção."""
    state = PetState()
    pet = PetWindow(100, 100, state)
    pet.show()
    try:
        plataforma.garantir_topo(int(pet.winId()))
    finally:
        pet.close()


def test_pet_manter_no_topo_chama_raise_e_garantir_topo(qapp):
    """Valida que pet.manter_no_topo chama raise_() e plataforma.garantir_topo."""
    state = PetState()
    pet = PetWindow(100, 100, state)
    pet.show()
    try:
        with patch.object(pet, "raise_") as mock_raise, \
             patch("pestinha.plataforma.garantir_topo") as mock_garantir:
            pet.manter_no_topo()
            assert mock_raise.called, "Deveria chamar self.raise_()"
            assert mock_garantir.called, "Deveria chamar plataforma.garantir_topo"
    finally:
        pet.close()


def test_manter_no_topo_ignorado_se_invisivel(qapp):
    """Quando o pet está oculto, manter_no_topo não deve forçar visibilidade ou raise."""
    state = PetState()
    pet = PetWindow(100, 100, state)
    pet.hide()
    try:
        with patch.object(pet, "raise_") as mock_raise:
            pet.manter_no_topo()
            assert not mock_raise.called
    finally:
        pet.close()

