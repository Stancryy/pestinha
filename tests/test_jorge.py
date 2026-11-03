"""
Etapa 4 do multipet + Etapa 6 (Mia): personagem Mia feita de configuração e conteúdo próprio,
e suporte completo a múltiplos personagens quando criados na pasta pets/.
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


def test_mia_existe_e_e_selecionavel():
    assert config.list_pets(PATHS) == ["mia"]
    mia = config.load_pet(PATHS, "mia")
    assert mia["nome"] == "Mia" and mia["seed"] == 42
    assert len(mia["temperamento"]) >= 8


def test_todo_temperamento_mexe_em_uma_ligacao_que_existe():
    """Uma chave com erro de digitação seria ignorada em silêncio; aqui ela falha."""
    validas = {f"{pre}->{post}" for pre, post, _w, _d in CONNECTIONS if pre in SENSORY_SPEC} | POOLS
    chaves = set(config.load_pet(PATHS, "mia")["temperamento"])
    assert chaves <= validas, chaves - validas


def test_mesmo_cerebro_outro_temperamento():
    mia = config.load_pet(PATHS, "mia")
    com = LIFBrain(seed=mia["seed"], temperament=mia["temperamento"])
    sem = LIFBrain(seed=mia["seed"])
    outro = LIFBrain(seed=7)
    assert com.W.shape == outro.W.shape and com.N == outro.N
    assert all(com.pool(m[0]) == outro.pool(m[0]) for m in MOTOR_SPEC)

    def bloco(cerebro, pre, post):
        a, b = cerebro.pool(pre), cerebro.pool(post)
        return cerebro.W[a["start"]:a["start"] + a["n"], b["start"]:b["start"] + b["n"]].sum()

    for chave, ganho in mia["temperamento"].items():
        pre, post = chave.split("->")
        assert np.isclose(bloco(com, pre, post), ganho * bloco(sem, pre, post)), chave
    assert np.isclose(bloco(com, "PRESO", "FRUSTRATION"), bloco(sem, "PRESO", "FRUSTRATION"))


def test_mia_tem_conteudo_proprio_completo():
    c = PATHS.conteudo("mia")
    placas = load_signs(c.signs)
    with open(c.signs, encoding="utf-8") as f:
        secoes = set(re.findall(r"^\[(\w+)\]", f.read(), re.M))
    assert secoes == set(DEFAULT_SIGNS)
    assert all(placas[s] for s in DEFAULT_SIGNS)
    assert config.Notes(c.notes).pick() and config.Notes(c.notes_sad).pick()
    assert (c.sprites / "feliz.webp").exists() and (c.sprites / "dormindo.webp").exists()
    assert c.bolinha_tenis.parent == PATHS.comum and c.notebook.parent == PATHS.comum


def test_sem_links_ou_dados_pessoais():
    """Nada de link externo, chave de PIX ou e-mail nas falas."""
    for texto in frases("mia"):
        assert not re.search(r"https?://|www\.|\.com\b|R\$\s*\d|chave pix|@\w+\.\w+", texto, re.I), texto


def test_mia_no_app(tmp_path, monkeypatch):
    QApplication.instance() or QApplication([])
    import shutil
    import pestinha.app as app_mod
    shutil.copytree(PATHS.pets, tmp_path / "pets")
    shutil.copytree(PATHS.comum, tmp_path / "assets" / "comum")
    paths = Paths(root=tmp_path)
    SettingsStore(paths).update(dict(config.DEFAULT_PERMISSIONS, pet="mia"))
    monkeypatch.setattr(app_mod, "PanicHotkey", lambda: SimpleNamespace(ok=True, pressed=Mock()))
    app = app_mod.PestinhaApp(SettingsStore(paths), paths)
    for timer in app.findChildren(app_mod.QTimer):
        timer.stop()
    mia = frases("mia")
    assert app.nome == "Mia" and app.pet_paths == paths.pet("mia")
    assert app.tray.icon.toolTip().startswith("Pestinha · Mia")
    assert app.revolucao.sprite is not None
    assert app.mischief.notes.pick() in mia
    assert set(app.castigo.cartazes) <= mia and set(app.castigo.xingamentos) <= mia
    for secao in DEFAULT_SIGNS:
        assert app.protest.pick(secao) in mia
    assert "meme" in app.mischief.available("feliz", dict(app.perms, travessuras=True, memes=True))
