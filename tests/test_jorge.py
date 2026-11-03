"""
Etapa 4 do multipet + Etapa 6 (Mia & Zuric): dois personagens feitos só de configuração e conteúdo.

Mesma rede e mesmos estágios; muda a semente, o temperamento (pets/mia.json e pets/zuric.json) e o
conteúdo (pets/mia/ e pets/zuric/). Nada da Mia aparece na Zuric, e nada da Zuric na Mia.
"""
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from pestinha import config  # noqa: E402
from pestinha.core.nervous_system import CONNECTIONS, MOTOR_SPEC, SENSORY_SPEC, LIFBrain  # noqa: E402
from pestinha.core.protesto import DEFAULT_SIGNS, load_signs  # noqa: E402
from pestinha.paths import Paths  # noqa: E402
from pestinha.settings_store import SettingsStore  # noqa: E402

PATHS = Paths(root=ROOT)
POOLS = {post for _pre, post, _w, _d in CONNECTIONS}


def frases(pet_id):
    """Tudo que o pet escreve: cartazes (todas as seções), recadinhos e bilhetes tristes."""
    c = PATHS.conteudo(pet_id)
    textos = {t for lista in load_signs(c.signs).values() for t in lista}
    for arquivo in (c.notes, c.notes_sad):
        textos |= {linha.strip() for linha in arquivo.read_text(encoding="utf-8").splitlines()
                   if linha.strip() and not linha.lstrip().startswith("#")}
    return textos


def test_mia_e_zuric_existem_e_sao_selecionaveis():
    assert config.list_pets(PATHS) == ["mia", "zuric"]
    mia = config.load_pet(PATHS, "mia")
    zuric = config.load_pet(PATHS, "zuric")
    assert mia["nome"] == "Mia" and zuric["nome"] == "Zuric"
    assert zuric["seed"] != mia["seed"]
    assert len(mia["temperamento"]) >= 8 and len(zuric["temperamento"]) >= 8


def test_todo_temperamento_mexe_em_uma_ligacao_que_existe():
    """Uma chave com erro de digitação seria ignorada em silêncio; aqui ela falha."""
    validas = {f"{pre}->{post}" for pre, post, _w, _d in CONNECTIONS if pre in SENSORY_SPEC} | POOLS
    for pet in ("mia", "zuric"):
        chaves = set(config.load_pet(PATHS, pet)["temperamento"])
        assert chaves <= validas, (pet, chaves - validas)


def test_mesmo_cerebro_outro_temperamento():
    zuric = config.load_pet(PATHS, "zuric")
    com = LIFBrain(seed=zuric["seed"], temperament=zuric["temperamento"])
    sem = LIFBrain(seed=zuric["seed"])
    pet_app = LIFBrain(seed=42, temperament=config.load_pet(PATHS, "mia")["temperamento"])
    assert com.W.shape == pet_app.W.shape and com.N == pet_app.N   # mesma estrutura
    assert all(com.pool(m[0]) == pet_app.pool(m[0]) for m in MOTOR_SPEC)

    def bloco(cerebro, pre, post):
        a, b = cerebro.pool(pre), cerebro.pool(post)
        return cerebro.W[a["start"]:a["start"] + a["n"], b["start"]:b["start"] + b["n"]].sum()

    for chave, ganho in zuric["temperamento"].items():           # cada ganho chega na ligação certa
        pre, post = chave.split("->")
        assert np.isclose(bloco(com, pre, post), ganho * bloco(sem, pre, post)), chave
    assert np.isclose(bloco(com, "PRESO", "FRUSTRATION"), bloco(sem, "PRESO", "FRUSTRATION"))  # o resto igual


def test_zuric_tem_conteudo_proprio_completo():
    c = PATHS.conteudo("zuric")
    placas = load_signs(c.signs)
    with open(c.signs, encoding="utf-8") as f:
        secoes = set(re.findall(r"^\[(\w+)\]", f.read(), re.M))
    assert secoes == set(DEFAULT_SIGNS)                          # não cai no neutro em nenhuma seção
    assert all(placas[s] for s in DEFAULT_SIGNS)
    assert config.Notes(c.notes).pick() and config.Notes(c.notes_sad).pick()
    assert c.bolinha_papel == PATHS.pets / "zuric" / "bolinha_papel.webp"
    assert c.bolinha_tenis.parent == PATHS.comum and c.notebook.parent == PATHS.comum


def test_nada_exclusivo_de_um_aparece_no_outro():
    neutras = {t for lista in DEFAULT_SIGNS.values() for t in lista}
    em_comum = frases("zuric") & frases("mia")
    assert em_comum <= neutras, em_comum - neutras
    textos_zuric = " ".join(frases("zuric")).upper()
    assert "MIA" not in textos_zuric
    textos_mia = " ".join(frases("mia")).upper()
    assert "ZURIC" not in textos_mia


def test_sem_links_ou_dados_pessoais():
    """Nada de link externo, chave de PIX ou e-mail nas falas."""
    for pet_id in ("mia", "zuric"):
        for texto in frases(pet_id):
            assert not re.search(r"https?://|www\.|\.com\b|R\$\s*\d|chave pix|@\w+\.\w+", texto, re.I), texto


def test_zuric_no_app(tmp_path, monkeypatch):
    QApplication.instance() or QApplication([])
    import shutil
    import pestinha.app as app_mod
    shutil.copytree(PATHS.pets, tmp_path / "pets")
    shutil.copytree(PATHS.comum, tmp_path / "assets" / "comum")
    paths = Paths(root=tmp_path)
    SettingsStore(paths).update(dict(config.DEFAULT_PERMISSIONS, pet="zuric"))
    monkeypatch.setattr(app_mod, "PanicHotkey", lambda: SimpleNamespace(ok=True, pressed=Mock()))
    app = app_mod.PestinhaApp(SettingsStore(paths), paths)
    for timer in app.findChildren(app_mod.QTimer):
        timer.stop()
    zuric = frases("zuric")
    assert app.nome == "Zuric" and app.pet_paths == paths.pet("zuric")
    assert app.tray.icon.toolTip().startswith("Pestinha · Zuric")
    assert app.revolucao.sprite is not None
    assert app.mischief.notes.pick() in zuric
    assert set(app.castigo.cartazes) <= zuric and set(app.castigo.xingamentos) <= zuric
    for secao in DEFAULT_SIGNS:
        assert app.protest.pick(secao) in zuric
    assert "meme" in app.mischief.available("feliz", dict(app.perms, travessuras=True, memes=True))
