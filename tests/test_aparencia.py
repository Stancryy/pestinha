"""
Etapa 5 do multipet + Etapa 6 (Mia & Zuric): cores, estilo (tv / anime_pixel) e acessórios por pet.

Um pet sem "aparencia" no .json fica idêntico ao PADRAO original. Valor inválido nunca derruba o app:
cor fora de #rrggbb, estilo desconhecido e acessório desconhecido ficam com o padrão.
"""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QColor, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from pestinha import config  # noqa: E402
from pestinha.body.desenho_rosto import (  # noqa: E402
    BODY_H, EYE, FRAME, PADRAO, SCREEN, SHELL, SHINE, aparencia_de, draw_face,
)
from pestinha.body.pet import CX, CY, WIN  # noqa: E402
from pestinha.core.emotion import EYE_SHAPES  # noqa: E402
from pestinha.paths import Paths  # noqa: E402
from pestinha.settings_store import SettingsStore  # noqa: E402

PATHS = Paths(root=ROOT)


def pintar(aparencia, emocao="observando", blink=1.0, carinho=False):
    """O rosto como a janela do pet pinta: 200x200, centro em (CX, CY)."""
    QApplication.instance() or QApplication([])
    img = QImage(WIN, WIN, QImage.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.translate(CX, CY)
    draw_face(p, dict(EYE_SHAPES[emocao]), (0.0, 0.0), blink, emocao, carinho=carinho, aparencia=aparencia)
    p.end()
    return img


def pixels_de(img, cor, tolerancia=40):
    alvo = QColor(cor)
    achados = []
    for y in range(img.height()):
        for x in range(img.width()):
            c = QColor(img.pixel(x, y))
            if (abs(c.red() - alvo.red()) + abs(c.green() - alvo.green()) + abs(c.blue() - alvo.blue()) < tolerancia
                    and QColor.fromRgba(img.pixel(x, y)).alpha() > 200):
                achados.append((x, y))
    return achados


def test_pet_sem_aparencia_continua_com_o_visual_original():
    a = aparencia_de(None)
    assert (a.moldura, a.casca, a.tela, a.olho, a.brilho) == (FRAME, SHELL, SCREEN, EYE, SHINE)
    assert a.estilo == "tv"
    assert a.acessorios == ()
    assert pintar(a) == pintar(PADRAO)


def test_valor_invalido_fica_com_o_padrao():
    a = aparencia_de({"estilo": "3d_inexistente", "moldura": "vermelho", "olho": "#12345", "tela": 7, "casca": "#AbCdEf",
                      "acessorios": {"chapeu": "#ffffff", "gravata": "azul", "oculos": "#000000"}})
    assert a.estilo == "tv"
    assert a.moldura == FRAME and a.olho == EYE and a.tela == SCREEN
    assert a.casca == QColor("#abcdef")
    assert [n for n, _c in a.acessorios] == ["oculos", "gravata"]            # chapéu não existe; ordem fixa
    assert dict(a.acessorios)["gravata"] == QColor("#b3261e")               # cor ruim: a padrão do acessório
    for ruim in (None, [], "x", {"acessorios": ["oculos"]}):
        assert aparencia_de(ruim).acessorios == ()


def test_mia_e_zuric_desenham_anime_pixel_com_headset_e_chifrinhos():
    for pet_id in ("mia", "zuric"):
        a = aparencia_de(config.load_pet(PATHS, pet_id)["aparencia"])
        assert a.estilo == "anime_pixel"
        assert [n for n, _c in a.acessorios] == ["headset", "chifrinhos"]
        casos = [(e, 1.0, False) for e in EYE_SHAPES] + [("observando", 0.08, False), ("feliz", 1.0, True)]
        cor_chifre = dict(a.acessorios)["chifrinhos"]
        for emocao, blink, carinho in casos:
            img = pintar(a, emocao, blink, carinho)
            assert pixels_de(img, a.moldura), (pet_id, emocao)
            assert pixels_de(img, cor_chifre), (pet_id, emocao)


def test_estilo_tv_desenha_gravata_dentro_do_corpo():
    a = aparencia_de({
        "moldura": "#e2b13c", "casca": "#14120c", "tela": "#1c1a12",
        "olho": "#ffd166", "brilho": "#fff3c4",
        "acessorios": {"gravata": "#b3261e"},
    })
    gravata = dict(a.acessorios)["gravata"]
    img = pintar(a, "observando", 1.0, False)
    pontos = pixels_de(img, gravata)
    assert pontos
    assert min(y for _x, y in pontos) >= CY
    assert max(y for _x, y in pontos) <= CY + BODY_H / 2 + 2


def test_aparencia_chega_na_janela_do_pet(tmp_path, monkeypatch):
    QApplication.instance() or QApplication([])
    import shutil
    import pestinha.app as app_mod
    shutil.copytree(PATHS.pets, tmp_path / "pets")
    paths = Paths(root=tmp_path)
    monkeypatch.setattr(app_mod, "PanicHotkey", lambda: SimpleNamespace(ok=True, pressed=Mock()))
    for pet in ("mia", "zuric"):
        SettingsStore(paths).update(dict(config.DEFAULT_PERMISSIONS, pet=pet))
        app = app_mod.PestinhaApp(SettingsStore(paths), paths)
        for timer in app.findChildren(app_mod.QTimer):
            timer.stop()
        assert app.pet.aparencia.estilo == "anime_pixel"
        assert bool(app.pet.aparencia.acessorios) is True
        app.pet.grab()                                                     # pinta de verdade, sem erro
