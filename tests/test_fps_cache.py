"""Testes para cache de QPixmap, resolução de imagens WebP/PNG e FPS adaptativo."""

from types import SimpleNamespace
from unittest.mock import Mock

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from pestinha import config
from pestinha.ajustes import (
    INTERVALO_QUADRO_ATIVO_MS,
    INTERVALO_QUADRO_DORMINDO_MS,
    INTERVALO_QUADRO_PARADO_MS,
)
from pestinha.body.bolinha import _PIXMAP_CACHE, carregar_pixmap
from pestinha.paths import Paths
from pestinha.settings_store import SettingsStore

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7V\xbd\xfa\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_carregar_pixmap_usa_cache_e_invalida_ao_mudar(tmp_path):
    QApplication.instance() or QApplication([])
    _PIXMAP_CACHE.clear()
    arq = tmp_path / "img.png"
    img = QImage(8, 8, QImage.Format_ARGB32)
    img.fill(0xFF00FF00)
    img.save(str(arq), "PNG")

    p1 = carregar_pixmap(arq, 32, 32)
    p2 = carregar_pixmap(arq, 32, 32)
    assert p1 is not None and p1 is p2
    assert len(_PIXMAP_CACHE) == 1

    # Arquivo inexistente ou corrompido devolve None
    assert carregar_pixmap(tmp_path / "inexistente.png", 32, 32) is None
    ruim = tmp_path / "corrompido.png"
    ruim.write_bytes(b"lixo")
    assert carregar_pixmap(ruim, 32, 32) is None


def test_resolver_imagem_prefere_webp_sobre_png(tmp_path):
    paths = Paths(root=tmp_path)
    paths.comum.mkdir(parents=True)
    (paths.comum / "bolinha_tenis.png").write_bytes(PNG)
    c = paths.conteudo("teste")
    assert c.bolinha_tenis == paths.comum / "bolinha_tenis.png"

    (paths.comum / "bolinha_tenis.webp").write_bytes(PNG)
    assert c.bolinha_tenis == paths.comum / "bolinha_tenis.webp"


def test_fps_adaptativo_muda_intervalo_conforme_estado(tmp_path, monkeypatch):
    QApplication.instance() or QApplication([])
    import pestinha.app as app_mod

    monkeypatch.setattr(app_mod, "PanicHotkey", lambda: SimpleNamespace(ok=True, pressed=Mock()))
    paths = Paths(root=tmp_path)
    (paths.pets / "teste").mkdir(parents=True)
    (paths.pets / "teste.json").write_text('{"nome": "Teste", "seed": 7}', encoding="utf-8")
    store = SettingsStore(paths)
    store.update(dict(config.DEFAULT_PERMISSIONS, pet="teste", ativo=True))
    app = app_mod.PestinhaApp(store, paths)
    try:
        # Em movimento no ar -> FPS ativo
        app.pet.body.grounded = False
        app.pet.body.vy = 150.0
        app._ajustar_fps()
        assert app.frame_timer.interval() == INTERVALO_QUADRO_ATIVO_MS

        # Parado no chão -> FPS parado (~20 fps)
        app.pet.body.grounded = True
        app.pet.body.vx = 0.0
        app.pet.body.vy = 0.0
        app.behavior.mission = None
        app.ball.hide()
        app._ajustar_fps()
        assert app.frame_timer.interval() == INTERVALO_QUADRO_PARADO_MS

        # Dormindo e parado -> FPS dormindo (~5 fps)
        app.sleep.asleep = True
        app._ajustar_fps()
        assert app.frame_timer.interval() == INTERVALO_QUADRO_DORMINDO_MS
    finally:
        for t in app.findChildren(app_mod.QTimer):
            t.stop()
