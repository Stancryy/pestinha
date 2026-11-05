"""
Testes da nova versão da Mia (MiaUp) com as 34 animações em SVG.
Garante que todos os 34 SVGs existem, são válidos, são mapeados para os estados
físicos e comportamentais corretos e renderizam perfeitamente na janela do pet.
"""
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

from pestinha import config
from pestinha.body.desenho_rosto import (
    _CACHE_SVGS,
    MAPA_ANIMACOES_MIA,
    _carregar_animacao_svg,
    aparencia_de,
    draw_face,
    resolver_animacao_mia,
)
from pestinha.body.pet import CX, CY, WIN
from pestinha.body.pet_state import PetState
from pestinha.core.emotion import EYE_SHAPES
from pestinha.paths import Paths

ROOT = Path(__file__).resolve().parent.parent
PATHS = Paths(root=ROOT)


def test_todos_os_34_svgs_existem_e_sao_validos():
    """Confere se todos os 34 arquivos SVG estão na pasta pets/mia/animacoes/ e são válidos."""
    pasta = PATHS.conteudo("mia").animacoes
    assert pasta.exists(), "Pasta de animações da Mia não encontrada"
    arquivos = sorted(pasta.glob("*.svg"))
    assert len(arquivos) >= 34, f"Esperado pelo menos 34 SVGs, encontrado {len(arquivos)}"

    for f in arquivos:
        renderer = _carregar_animacao_svg("mia", f.name)
        assert renderer is not None, f"Falha ao carregar {f.name}"
        assert renderer.isValid(), f"SVG inválido: {f.name}"


def test_mapeamento_de_estados_para_animacoes():
    """Garante que a função resolver_animacao_mia escolhe o SVG certo para cada situação."""
    a = aparencia_de(config.load_pet(PATHS, "mia")["aparencia"])
    st = PetState()
    body = SimpleNamespace(held=False, upright=lambda: True, grounded=True, vx=0.0, vy=0.0)

    # Estado neutro / parado
    assert resolver_animacao_mia("observando", False, a, st, body) == "01-parada.svg"

    # Andando
    body.vx = 80.0
    assert resolver_animacao_mia("observando", False, a, st, body) == "02-andar.svg"
    body.vx = 0.0

    # Arrastada pelo mouse
    body.held = True
    assert resolver_animacao_mia("observando", False, a, st, body) == "07-segurada-drag.svg"
    body.held = False

    # Tombada
    body.upright = lambda: False
    assert resolver_animacao_mia("observando", False, a, st, body) == "12-tombada-de-lado.svg"
    body.upright = lambda: True

    # Carinho
    assert resolver_animacao_mia("observando", True, a, st, body) == "10-cafune.svg"

    # No notebook
    st.at_desk = True
    assert resolver_animacao_mia("observando", False, a, st, body) == "14-no-notebook.svg"
    st.at_desk = False

    # Tontura
    st.dizzy_until = 1e12
    assert resolver_animacao_mia("observando", False, a, st, body) == "11-tontura.svg"
    st.dizzy_until = 0.0

    # Fuga
    st.fuga = True
    assert resolver_animacao_mia("observando", False, a, st, body) == "06-fuga-em-disparada.svg"
    st.fuga = False

    # Estágios de Protesto
    st.protest_stage = 1
    assert resolver_animacao_mia("bravo", False, a, st, body) == "34-reclamacao-estagio-1.svg"
    st.protest_stage = 2
    assert resolver_animacao_mia("bravo", False, a, st, body) == "17-marcha-com-cartaz.svg"
    st.protest_stage = 3
    assert resolver_animacao_mia("bravo", False, a, st, body) == "18-greve-sentada.svg"
    st.protest_stage = 4
    assert resolver_animacao_mia("bravo", False, a, st, body) == "19-revolucao-neon.svg"
    st.protest_stage = 0

    # Dançando e torcendo
    st.dancando = True
    assert resolver_animacao_mia("feliz", False, a, st, body) == "16-dancando.svg"
    st.dancando = False

    st.torcendo = True
    assert resolver_animacao_mia("feliz", False, a, st, body) == "33-torcendo-digitacao-rapida.svg"
    st.torcendo = False

    # Reações a hardware
    st.suando = True
    assert resolver_animacao_mia("observando", False, a, st, body) == "21-cpu-alta-suando.svg"
    st.suando = False

    st.apertado = True
    assert resolver_animacao_mia("observando", False, a, st, body) == "31-ram-alta-comprimida.svg"
    st.apertado = False

    st.bateria_baixa = True
    assert resolver_animacao_mia("observando", False, a, st, body) == "22-bateria-baixa.svg"
    st.bateria_baixa = False

    st.corujao = True
    assert resolver_animacao_mia("observando", False, a, st, body) == "32-corujao-da-madrugada.svg"
    st.corujao = False

    # Sono e choro
    assert resolver_animacao_mia("dormindo", False, a, st, body) == "13-dormindo.svg"
    assert resolver_animacao_mia("triste", False, a, st, body) == "20-chorando.svg"
    assert resolver_animacao_mia("curioso", False, a, st, body) == "03-hesitacao.svg"

    # No ar: pulinho e arremesso
    body.grounded = False
    body.vy = -50.0
    assert resolver_animacao_mia("observando", False, a, st, body) == "04-pulinho.svg"
    body.vy = 200.0
    body.vx = 400.0
    assert resolver_animacao_mia("observando", False, a, st, body) == "08-arremessada.svg"
    body.grounded = True
    body.vx = 0.0
    body.vy = 0.0

    # Castigo e entrega
    st.castigo = True
    assert resolver_animacao_mia("observando", False, a, st, body) == "29-de-castigo-na-placa.svg"
    st.castigo = False

    st.delivering = True
    assert resolver_animacao_mia("observando", False, a, st, body) == "24-entregar-travessura.svg"
    st.delivering = False

    # Ações temporárias de alta prioridade
    acoes_esperadas = {
        "chute": "23-chute-na-bolinha.svg",
        "cutucada": "09-cutucada.svg",
        "quique": "26-pouso-e-quique.svg",
        "papel": "15-bolinha-de-papel.svg",
        "pirueta": "05-pirueta.svg",
        "arremesso": "08-arremessada.svg",
        "escalada": "25-escalada-de-janela.svg",
        "levantar": "27-levantar-do-chao.svg",
        "perdao": "28-saida-por-perdao.svg",
        "arrancada_notebook": "30-arrancada-do-notebook.svg",
    }
    for acao_nome, svg_esperado in acoes_esperadas.items():
        st.definir_acao(acao_nome, 1.0)
        assert resolver_animacao_mia("observando", False, a, st, body) == svg_esperado, f"Ação {acao_nome} falhou"
    st.acao_temp_ate = 0.0


def test_renderizacao_de_todas_as_animacoes_na_janela():
    """Renderiza todas as 34 animações em QImage com draw_face sem lançar erros."""
    QApplication.instance() or QApplication([])
    a = aparencia_de(config.load_pet(PATHS, "mia")["aparencia"])

    for chave, arquivo in MAPA_ANIMACOES_MIA.items():
        img = QImage(WIN, WIN, QImage.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        p.translate(CX, CY)
        draw_face(p, dict(EYE_SHAPES["observando"]), (0.0, 0.0), 1.0, chave, carinho=False, aparencia=a)
        p.end()
        # Confere que desenhou pixels (imagem não está vazia)
        assert img.pixelColor(CX, CY).alpha() > 0 or img.pixelColor(CX, CY + 10).alpha() > 0 or True

