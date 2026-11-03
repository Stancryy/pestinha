"""Testes do gerador de frases via LLM local (Item 27) e do 2º pet simultâneo (Item 24)."""

import json
import urllib.request
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from pestinha import config
from pestinha.body.pet import PetWindow
from pestinha.body.pet_state import PetState
from pestinha.core.homeostasis import Drives
from pestinha.mind.llm_local import (
    GeradorLLMLocal,
    consultar_llm_local,
    eh_url_local_segura,
    limpar_frase_llm,
)
from pestinha.mind.segundo_pet import SegundoPetController
from pestinha.paths import Paths


def test_eh_url_local_segura_aceita_apenas_loopback():
    """Garante que apenas endereços de loopback locais (127.0.0.1, localhost, ::1) são permitidos."""
    assert eh_url_local_segura("http://127.0.0.1:11434") is True
    assert eh_url_local_segura("http://localhost:1234/v1") is True
    assert eh_url_local_segura("http://[::1]:11434") is True

    assert eh_url_local_segura("https://api.openai.com/v1") is False
    assert eh_url_local_segura("http://192.168.1.50:11434") is False
    assert eh_url_local_segura("ftp://127.0.0.1:11434") is False
    assert eh_url_local_segura("") is False


def test_limpar_frase_llm_remove_aspas_e_limita_tamanho():
    """Remove aspas externas, quebras de linha e trunca em 90 caracteres."""
    assert limpar_frase_llm('  "Eita, esse bug tá difícil!"\nOutra linha') == "Eita, esse bug tá difícil!"
    longo = "a" * 150
    res = limpar_frase_llm(longo)
    assert len(res) <= 90
    assert res.endswith("…")


def test_gerador_llm_local_sucesso_e_fallback(monkeypatch, tmp_path):
    """Usa o LLM local quando ativo e acessível, e cai para Notes.pick() se desligado ou falhar."""
    arq = tmp_path / "notes.txt"
    arq.write_text("Frase do arquivo txt\n", encoding="utf-8")
    notes = config.Notes(arq)

    ger = GeradorLLMLocal()
    # Desligado -> usa o .txt
    assert ger.escolher_frase(notes, ativo=False) == "Frase do arquivo txt"

    # URL externa bloqueada -> fallback imediato para .txt
    assert (
        ger.escolher_frase(notes, ativo=True, endpoint="https://example.com:11434", sincrono=True)
        == "Frase do arquivo txt"
    )

    # Simulando resposta local do Ollama
    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"response": '"Bora commitar logo isso aí!"'}).encode("utf-8")

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=1.5: FakeResp())
    frase = ger.escolher_frase(
        notes,
        ativo=True,
        endpoint="http://127.0.0.1:11434",
        modelo="llama3.2",
        nome_pet="Mia",
        sincrono=True,
    )
    assert frase == "Bora commitar logo isso aí!"

    # Simulando falha de conexão -> fallback para .txt
    def _erro(*_a, **_kw):
        raise OSError("servidor local desligado")

    monkeypatch.setattr(urllib.request, "urlopen", _erro)
    assert (
        consultar_llm_local("http://127.0.0.1:11434", "llama3.2", "Mia", "observando", "IDLE")
        is None
    )
    assert (
        ger.escolher_frase(notes, ativo=True, endpoint="http://127.0.0.1:11434", sincrono=True)
        == "Frase do arquivo txt"
    )


def test_segundo_pet_interage_brinca_e_briga(tmp_path):
    """Cria um 2º pet via Wizard, ativa SegundoPetController e verifica brincadeira e briga."""
    QApplication.instance() or QApplication([])
    paths = Paths(root=tmp_path)
    config.criar_pet_personalizado(paths, {"id": "mia", "nome": "Mia"})
    config.criar_pet_personalizado(paths, {"id": "parceiro", "nome": "Parceiro", "estilo_temperamento": "caotico"})

    ctl = SegundoPetController(paths, "mia")
    assert ctl.escolher_segundo_id() == "parceiro"

    bounds = (0, 0, 1920, 1080)
    areas = [bounds]
    ctl.sincronizar(ativo=True, visivel=True, bounds=bounds)
    assert ctl.janela is not None
    assert ctl.janela.isVisible() is True

    st_main = PetState()
    pet_main = PetWindow(500, 900, st_main)
    drives = Drives()
    ball = SimpleNamespace(isVisible=lambda: False, body=SimpleNamespace(x=0.0, y=0.0))

    try:
        # Coloca os dois pets pertinho (< 125 px) e calmos -> devem brincar
        pet_main.body.x, pet_main.body.y = 500.0, 900.0
        ctl.janela.body.x, ctl.janela.body.y = 540.0, 900.0
        ctl.ultima_interacao = -100.0
        st_main.emotion = "observando"
        st_main.protest_stage = 0

        evento = ctl.tick(
            0.016, 10.0, bounds, areas, areas, [], pet_main, st_main, drives, ball
        )
        assert evento == "brincar"
        assert ctl.estado.emotion == "feliz"

        # Coloca os dois pertinho com o pet principal bravo -> devem brigar
        pet_main.body.x, pet_main.body.y = 500.0, 900.0
        ctl.janela.body.x, ctl.janela.body.y = 530.0, 900.0
        ctl.ultima_interacao = -100.0
        st_main.emotion = "bravo"
        st_main.protest_stage = 2

        evento2 = ctl.tick(
            0.016, 20.0, bounds, areas, areas, [], pet_main, st_main, drives, ball
        )
        assert evento2 == "brigar"
        assert ctl.estado.emotion == "bravo"
    finally:
        ctl.fechar()
        pet_main.close()
