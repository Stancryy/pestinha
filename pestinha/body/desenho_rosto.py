"""
DESENHO DO ROSTO - só o que se desenha do pet: corpo/moldura, olhos, brilho, acessórios e os Zzz.

Suporta dois estilos visuais configuráveis em `aparencia.estilo` no `<pet>.json`:
- `"tv"` (padrão clássico): telinha arredondada com olhos expressivos.
- `"anime_pixel"`: garota de anime chibi em pixel art de alta densidade (usa sprites 32-bit de
  `pets/<variante>/sprites/<emocao>.webp` quando disponíveis, com fallback procedural em grade 2px
  de 5 tons, variantes distintas para Mia e Zuric, olhos detalhados com cílios e degradê na íris
  que seguem o cursor, boquinha com dentinho/fang, torso chibi com moletom/jaqueta, headset gamer
  e chifrinhos).
"""

import math
import re
from dataclasses import dataclass, field

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPolygonF

from ..ajustes import ZZZ_PERIODO as ZZZ_PERIOD, ZZZ_QUANTIDADE as ZZZ_COUNT
from ..paths import Paths

BODY_W, BODY_H = 120, 90
FRAME = QColor("#63e56f")
SHELL = QColor("#101512")
SCREEN = QColor("#171e19")
EYE = QColor("#3ee877")
SHINE = QColor("#c8ffd8")

ESTILOS_VALIDOS = ("tv", "anime_pixel")
VARIANTES_VALIDAS = ("mia", "zuric")
ACESSORIOS = ("oculos", "gravata", "headset", "chifrinhos", "bone", "gorro_natal", "chapeu_festa")
COR_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
COR_PADRAO_ACESSORIO = {
    "oculos": "#e8e8e8",
    "gravata": "#b3261e",
    "headset": "#00f0ff",
    "chifrinhos": "#ff2a85",
    "bone": "#3a86ff",
    "gorro_natal": "#d90429",
    "chapeu_festa": "#ffbe0b",
}

_CACHE_SPRITES = {}


def _carregar_sprite_anime(variante: str, chave: str):
    """Carrega (com cache) o sprite .webp de alta definição de pets/<variante>/sprites/<chave>.webp."""
    k = (variante, chave)
    if k in _CACHE_SPRITES:
        return _CACHE_SPRITES[k]
    caminho = Paths().conteudo(variante).sprites / f"{chave}.webp"
    if not caminho.exists():
        return None
    img = QImage(str(caminho))
    if img.isNull():
        return None
    _CACHE_SPRITES[k] = img
    return img


@dataclass(frozen=True)
class Aparencia:
    """Cores, estilo e acessórios do pet. O padrão é idêntico ao visual original."""
    moldura: QColor = field(default_factory=lambda: QColor(FRAME))
    casca: QColor = field(default_factory=lambda: QColor(SHELL))
    tela: QColor = field(default_factory=lambda: QColor(SCREEN))
    olho: QColor = field(default_factory=lambda: QColor(EYE))
    brilho: QColor = field(default_factory=lambda: QColor(SHINE))
    acessorios: tuple = ()          # ((nome, QColor), ...) na ordem de ACESSORIOS
    estilo: str = "tv"              # "tv" ou "anime_pixel"
    variante: str = "mia"           # "mia" (maria-chiquinha + moletom) ou "zuric" (wolf-cut + jaqueta)
    suando: bool = False            # reação visual a CPU alta (Etapa 9)
    apertado: bool = False          # reação visual a RAM cheia (Etapa 9)


PADRAO = Aparencia()


def _cor(valor, padrao):
    """Aceita só #rrggbb; qualquer outra coisa volta para a cor padrão."""
    return QColor(valor) if isinstance(valor, str) and COR_HEX.match(valor) else QColor(padrao)


def aparencia_de(dados):
    """Monta a Aparencia a partir do dict `aparencia` do `<pet>.json`. Tudo opcional; inválido vira padrão."""
    if not isinstance(dados, dict):
        return PADRAO
    brutos = dados.get("acessorios")
    acessorios = []
    if isinstance(brutos, dict):
        for nome in ACESSORIOS:
            if nome in brutos and brutos[nome]:
                acessorios.append((nome, _cor(brutos[nome], COR_PADRAO_ACESSORIO[nome])))
    estilo = dados.get("estilo", "tv")
    if estilo not in ESTILOS_VALIDOS:
        estilo = "tv"
    variante = dados.get("variante", "mia")
    if variante not in VARIANTES_VALIDAS:
        variante = "mia"
    return Aparencia(
        moldura=_cor(dados.get("moldura"), FRAME),
        casca=_cor(dados.get("casca"), SHELL),
        tela=_cor(dados.get("tela"), SCREEN),
        olho=_cor(dados.get("olho"), EYE),
        brilho=_cor(dados.get("brilho"), SHINE),
        acessorios=tuple(acessorios),
        estilo=estilo,
        variante=variante,
        suando=bool(dados.get("suando", False)),
        apertado=bool(dados.get("apertado", False)),
    )


def lerp_shape(current, target, k):
    """Interpola duas formas de olho: `k` entre 0 (atual) e 1 (alvo), para a transição ser suave."""
    return {key: current[key] + (target[key] - current[key]) * k for key in target}


def draw_face(p: QPainter, shape: dict, gaze=(0.0, 0.0), blink=1.0, emotion="observando",
              carinho=False, aparencia=PADRAO):
    """Desenha o pet (estilo clássico 'tv' ou 'anime_pixel') com centro na origem do painter."""
    a = aparencia or PADRAO
    p.save()
    if getattr(a, "apertado", False):
        p.scale(0.84, 1.08)
    if a.estilo == "anime_pixel":
        _draw_anime_pixel(p, shape, gaze, blink, emotion, carinho, a)
    else:
        _draw_tv(p, shape, gaze, blink, emotion, carinho, a)
    if getattr(a, "suando", False):
        _desenhar_gotas_suor(p)
    p.restore()


def _draw_tv(p: QPainter, shape: dict, gaze, blink: float, emotion: str, carinho: bool, a: Aparencia):
    """Desenho clássico da telinha com dois olhos e acessórios."""
    p.setPen(QPen(a.moldura, 5))
    p.setBrush(a.casca)
    p.drawRoundedRect(QRectF(-BODY_W / 2, -BODY_H / 2, BODY_W, BODY_H), 20, 20)
    p.setPen(Qt.NoPen)
    p.setBrush(a.tela)
    p.drawRoundedRect(QRectF(-BODY_W / 2 + 11, -BODY_H / 2 + 11, BODY_W - 22, BODY_H - 22), 12, 12)
    for nome, cor in a.acessorios:
        if nome == "gravata":
            _gravata(p, cor)

    if carinho:
        p.setPen(QPen(a.olho, 5, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        for side in (-1, 1):
            cx, cy = side * 24, shape["dy"]
            p.drawArc(QRectF(cx - 15, cy - 8, 30, 22), 0, 180 * 16)
        p.setPen(Qt.NoPen)
    else:
        _olhos(p, shape, gaze, blink, emotion, a)
    for nome, cor in a.acessorios:
        if nome == "oculos":
            _oculos(p, cor)
        elif nome == "headset":
            _headset(p, cor, a.casca)
        elif nome == "chifrinhos":
            _chifrinhos(p, cor)
        elif nome == "bone":
            _bone(p, cor)
        elif nome == "gorro_natal":
            _gorro_natal(p, cor)
        elif nome == "chapeu_festa":
            _chapeu_festa(p, cor)


# ============================================================
# ESTILO ANIME PIXEL ART DE ALTA DENSIDADE (MIA & ZURIC)
# ============================================================

def _draw_anime_pixel(p: QPainter, shape: dict, gaze, blink: float, emotion: str,
                      carinho: bool, a: Aparencia):
    """
    Desenha a personagem chibi de anime em pixel art detalhado:
    - Se houver sprite 32-bit em `pets/<variante>/sprites/<emocao>.webp`, renderiza o sprite
      com deslocamento suave pelo olhar (`gaze`) e detalhes de cor dos acessórios configurados.
    - Caso contrário, renderiza o pixel art procedural de grade fina (2px) em 5 tons.
    """
    p.save()
    p.setRenderHint(QPainter.Antialiasing, False)
    p.setPen(Qt.NoPen)

    acessorios_dict = dict(a.acessorios)
    chave_sp = "carinho" if carinho else ("dormindo" if (emotion == "dormindo" or blink < 0.25) else emotion)
    sprite = _carregar_sprite_anime(a.variante, chave_sp)
    if sprite is not None:
        gx, gy = gaze
        dx = max(-1.0, min(1.0, gx)) * 3.0
        dy = max(-1.0, min(1.0, gy)) * 2.0
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        p.drawImage(QRectF(-68 + dx, -66 + dy, 136, 136), sprite)
        p.setRenderHint(QPainter.Antialiasing, False)
        # Pontos internos discretos para sincronizar as cores exatas configuradas em aparencia
        p.fillRect(QRectF(-2 + dx, -28 + dy, 3, 3), a.moldura)
        if "chifrinhos" in acessorios_dict:
            cor_ch = acessorios_dict["chifrinhos"]
            p.fillRect(QRectF(-26 + dx, -38 + dy, 2, 2), cor_ch)
            p.fillRect(QRectF(24 + dx, -38 + dy, 2, 2), cor_ch)
        if "headset" in acessorios_dict:
            cor_hs = acessorios_dict["headset"]
            p.fillRect(QRectF(-36 + dx, -6 + dy, 2, 4), cor_hs)
            p.fillRect(QRectF(34 + dx, -6 + dy, 2, 4), cor_hs)
        for nome in ("oculos", "gravata", "bone", "gorro_natal", "chapeu_festa"):
            if nome in acessorios_dict:
                _DESENHAR_ACESSORIO[nome](p, acessorios_dict[nome])
        p.restore()
        return

    u = 2.0  # cada unidade da grade = 2x2 pixels na tela (grade ~64x56)

    def px(gx, gy, gw, gh, color):
        p.setBrush(color)
        p.drawRect(QRectF(gx * u, gy * u, gw * u, gh * u))

    def mirror_px(gx, gy, gw, gh, color):
        px(gx, gy, gw, gh, color)
        px(-gx - gw, gy, gw, gh, color)

    c_hair = a.moldura
    c_out = QColor("#120824") if a.variante == "mia" else QColor("#071324")
    c_dark = c_hair.darker(210)
    c_mid = c_hair.darker(140)
    c_light = c_hair.lighter(130)
    c_rim = a.olho.lighter(120)

    c_skin_out = QColor("#8f5371")
    c_skin_shd = QColor("#ebb8d0")
    c_skin_mid = QColor("#f7d4e6")
    c_skin = QColor(a.tela) if a.tela != SCREEN else QColor("#fde6f2")
    c_blush = QColor("#ff6ea7")
    c_blush_hi = QColor("#ffa6c9")

    if a.variante == "mia":
        for s in (-1, 1):
            px(s * 20 - (4 if s < 0 else 0), -14, 4, 30, c_out)
            px(s * 23 - (5 if s < 0 else 0), -10, 5, 28, c_out)
            px(s * 25 - (4 if s < 0 else 0), -2, 4, 22, c_out)
            px(s * 19 - (4 if s < 0 else 0), -13, 4, 28, c_dark)
            px(s * 21 - (5 if s < 0 else 0), -11, 5, 27, c_mid)
            px(s * 22 - (4 if s < 0 else 0), -9, 4, 23, c_hair)
            px(s * 24 - (3 if s < 0 else 0), -1, 3, 19, c_hair)
            px(s * 23 - (2 if s < 0 else 0), -6, 2, 10, c_light)
            px(s * 22 - (3 if s < 0 else 0), 11, 3, 6, c_rim)
            px(s * 24 - (2 if s < 0 else 0), 13, 2, 5, c_rim)
            px(s * 18 - (4 if s < 0 else 0), -15, 4, 3, c_rim)
            px(s * 19 - (2 if s < 0 else 0), -16, 2, 5, c_light)
    else:
        c_tip = QColor("#ff2a85")
        for s in (-1, 1):
            px(s * 18 - (5 if s < 0 else 0), -14, 5, 26, c_out)
            px(s * 21 - (5 if s < 0 else 0), -11, 5, 10, c_out)
            px(s * 23 - (4 if s < 0 else 0), -8, 4, 5, c_out)
            px(s * 20 - (5 if s < 0 else 0), 2, 5, 12, c_out)
            px(s * 23 - (4 if s < 0 else 0), 6, 4, 6, c_out)
            px(s * 17 - (4 if s < 0 else 0), -13, 4, 24, c_dark)
            px(s * 19 - (4 if s < 0 else 0), -10, 4, 18, c_mid)
            px(s * 20 - (4 if s < 0 else 0), -9, 4, 8, c_hair)
            px(s * 22 - (3 if s < 0 else 0), -7, 3, 3, c_light)
            px(s * 19 - (4 if s < 0 else 0), 4, 4, 9, c_tip.darker(130))
            px(s * 21 - (3 if s < 0 else 0), 6, 3, 5, c_tip)

    px(-17, -18, 34, 30, c_out)
    px(-16, -17, 32, 28, c_dark)
    px(-4, 10, 8, 5, c_skin_out)
    px(-3, 10, 6, 4, c_skin_shd)

    if a.variante == "mia":
        c_hoodie = QColor("#1f1138")
        c_hoodie_hi = QColor("#351e5e")
        px(-15, 13, 30, 11, c_out)
        px(-14, 14, 28, 9, c_hoodie)
        px(-12, 14, 24, 3, c_hoodie_hi)
        mirror_px(8, 12, 6, 4, c_out)
        mirror_px(8, 13, 5, 3, c_mid)
        px(-4, 13, 8, 4, c_light)
        px(-2, 14, 4, 4, c_rim)
        px(-1, 17, 2, 6, c_out)
        mirror_px(4, 15, 1, 7, c_rim)
        mirror_px(4, 21, 2, 2, QColor("#ffffff"))
    else:
        c_jkt = QColor("#0f192e")
        c_jkt_hi = QColor("#1c2e52")
        c_neon = QColor("#ff2a85")
        px(-3, 12, 6, 1, c_out)
        px(-1, 12, 2, 2, c_neon)
        px(-16, 13, 32, 11, c_out)
        px(-15, 14, 30, 9, c_jkt)
        px(-10, 12, 20, 4, c_out)
        px(-9, 13, 18, 3, c_jkt_hi)
        mirror_px(10, 15, 4, 2, c_neon)
        mirror_px(6, 17, 2, 6, c_hair)
        px(-2, 15, 4, 8, c_out)
        px(-1, 16, 2, 6, c_neon)

    mirror_px(15, -3, 3, 6, c_skin_out)
    mirror_px(15, -2, 2, 4, c_skin_shd)
    px(-15, -15, 30, 25, c_skin_out)
    px(-13, 10, 26, 2, c_skin_out)
    px(-10, 11, 20, 1, c_skin_out)
    px(-14, -14, 28, 23, c_skin)
    px(-12, 9, 24, 2, c_skin)
    px(-12, 8, 24, 2, c_skin_shd)
    px(-9, 10, 18, 1, c_skin_shd)
    mirror_px(13, -6, 1, 14, c_skin_shd)
    px(-14, -12, 28, 3, c_skin_mid)

    blush_intenso = carinho or emotion in ("feliz", "contente", "dramatico")
    for s in (-1, 1):
        bx = s * 10 - (4 if s < 0 else 0)
        px(bx, 3, 4, 2, c_blush if blush_intenso else c_skin_shd)
        if blush_intenso:
            px(bx - 1, 4, 6, 2, c_blush)
            px(bx + 1, 3, 1, 2, c_blush_hi)
            px(bx + 3, 4, 1, 2, c_blush_hi)

    gx, gy = gaze
    ox_shift = int(round(max(-1.0, min(1.0, gx)) * 2.0))
    oy_shift = int(round(max(-1.0, min(1.0, gy)) * 1.5))

    for side in (-1, 1):
        cx = side * 8
        cy = -1
        if emotion == "dormindo" or blink < 0.25:
            px(cx - 4, cy, 8, 1, c_out)
            px(cx - 3, cy + 1, 6, 1, c_out)
            px(cx + (3 if side > 0 else -5), cy - 1, 2, 1, c_out)
        elif carinho:
            px(cx - 3, cy - 2, 6, 1, c_out)
            px(cx - 4, cy - 1, 2, 2, c_out)
            px(cx + 2, cy - 1, 2, 2, c_out)
        else:
            px(cx - 4, cy - 4, 8, 8, QColor("#ffffff"))
            px(cx - 4, cy - 4, 8, 2, QColor("#d9d2e8"))
            ix = cx - 2 + ox_shift
            iy = cy - 3 + oy_shift
            px(ix, iy, 5, 2, a.olho.darker(190))
            px(ix, iy + 2, 5, 2, a.olho.darker(125))
            px(ix, iy + 4, 5, 2, a.olho)
            px(ix + 1, iy + 5, 3, 2, a.olho.lighter(145))
            if a.variante == "zuric":
                px(ix + 2, iy + 1, 1, 4, c_out)
            else:
                px(ix + 1, iy + 2, 3, 2, c_out)
                px(ix + 2, iy + 1, 1, 4, c_out)
            px(ix, iy + 1, 2, 2, a.brilho)
            px(ix + 3, iy + 4, 1, 1, a.brilho)
            px(cx - 4, cy - 6, 8, 1, c_skin_out)
            px(cx - 5, cy - 5, 10, 2, c_out)
            px(cx - 3, cy + 4, 6, 1, c_skin_out)

    px(0, 2, 1, 1, c_skin_out)
    if emotion in ("feliz", "contente") or carinho:
        px(-3, 5, 3, 1, c_skin_out)
        px(0, 4, 1, 1, c_skin_out)
        px(1, 5, 3, 1, c_skin_out)
        px(2, 6, 1, 2, QColor("#ffffff"))
    elif emotion == "bravo":
        px(-3, 4, 6, 4, c_out)
        px(-2, 5, 4, 1, QColor("#ffffff"))
        px(-2, 6, 4, 2, QColor("#d9386a"))
    elif emotion == "triste":
        px(-2, 5, 4, 1, c_skin_out)
        for s in (-1, 1):
            px(s * 8 - 1, 3, 2, 5, QColor("#4ddbff"))
    else:
        px(-2, 5, 4, 1, c_skin_out)

    px(-17, -21, 34, 4, c_out)
    px(-15, -23, 30, 2, c_out)
    px(-16, -20, 32, 7, c_dark)
    px(-15, -21, 30, 6, c_mid)
    px(-14, -19, 28, 6, c_hair)
    px(-11, -17, 6, 2, c_light)
    px(-3, -18, 6, 2, c_light)
    px(5, -17, 6, 2, c_light)
    px(-2, -17, 4, 1, a.brilho)

    if "chifrinhos" in acessorios_dict:
        cor_ch = acessorios_dict["chifrinhos"]
        for s in (-1, 1):
            px(s * 9 - (3 if s < 0 else 0), -24, 3, 4, cor_ch.darker(160))
            px(s * 10 - (2 if s < 0 else 0), -27, 2, 4, cor_ch)
            px(s * 11 - (1 if s < 0 else 0), -29, 1, 2, cor_ch.lighter(145))

    if "headset" in acessorios_dict:
        cor_hs = acessorios_dict["headset"]
        px(-16, -23, 32, 3, c_out)
        px(-10, -22, 20, 1, cor_hs)
        for s in (-1, 1):
            hx = s * 16 - (6 if s < 0 else 0)
            px(hx, -9, 6, 13, c_out)
            px(hx + (2 if s < 0 else 3), -6, 1, 7, cor_hs)

    for nome in ("oculos", "gravata", "bone", "gorro_natal", "chapeu_festa"):
        if nome in acessorios_dict:
            _DESENHAR_ACESSORIO[nome](p, acessorios_dict[nome])

    p.restore()


def _desenhar_gotas_suor(p: QPainter):
    """Gotinhas de suor azuis quando a CPU do PC está alta."""
    p.save()
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#4cc9f0"))
    p.drawEllipse(QPointF(42, -24), 4, 6)
    p.drawEllipse(QPointF(48, -12), 3, 5)
    p.restore()


# ============================================================
# OLHOS E ACESSÓRIOS DO MODO CLÁSSICO ("tv")
# ============================================================

def _olhos(p, shape, gaze, blink, emotion, a):
    """Desenha os dois olhos: forma, piscada, brilho e direção do olhar."""
    gx, gy = gaze
    for side in (-1, 1):
        w = shape["w"]
        h = shape["h"] * blink
        if emotion == "curioso" and side == 1:
            h *= 1.15
        h = max(h, 3.0)
        cx = side * 24 + gx * 4
        cy = shape["dy"] + gy * 3
        top = cy - h / 2

        eye = QPainterPath()
        eye.addRoundedRect(QRectF(cx - w / 2, top, w, h), min(w, h) * 0.38, min(w, h) * 0.38)

        if blink > 0.5:
            outer_x = cx + side * w / 2
            inner_x = cx - side * w / 2
            lid = QPainterPath()
            lid.addPolygon(
                QPolygonF(
                    [
                        QPointF(outer_x + side * 4, top - 40),
                        QPointF(inner_x - side * 4, top - 40),
                        QPointF(inner_x - side * 4, top + shape["inner"] * h),
                        QPointF(outer_x + side * 4, top + shape["outer"] * h),
                    ]
                )
            )
            eye = eye.subtracted(lid)
            if shape["smile"] > 0.02:
                cut = QPainterPath()
                ch = h * shape["smile"] * 1.6
                cut.addEllipse(QRectF(cx - w * 0.75, top + h - ch * 0.45, w * 1.5, ch))
                eye = eye.subtracted(cut)

        p.setBrush(a.olho)
        p.drawPath(eye)

        if blink > 0.5 and h >= 8:
            p.save()
            p.setClipPath(eye)
            p.setBrush(a.brilho)
            sx = cx - w * 0.18 + gx * 3
            sy = top + h * (0.24 + max(shape["inner"], shape["outer"]) * 0.6) + gy * 2
            p.drawEllipse(QPointF(sx, sy), 3.6, 3.6)
            p.restore()


def _oculos(p, cor):
    """Armação por cima dos olhos: aro grosso em cima, fino embaixo, e a ponte no meio."""
    p.save()
    p.setBrush(Qt.NoBrush)
    for side in (-1, 1):
        lente = QRectF(side * 24 - 21, -25, 42, 52)
        vidro = QColor(cor)
        vidro.setAlpha(22)
        p.setPen(Qt.NoPen)
        p.setBrush(vidro)
        p.drawRoundedRect(lente, 10, 10)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(cor, 2))
        p.drawRoundedRect(lente, 10, 10)
        p.setPen(QPen(cor, 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(lente.left() + 4, lente.top()), QPointF(lente.right() - 4, lente.top()))
    p.setPen(QPen(cor, 3, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(-3, -18), QPointF(3, -18))
    p.restore()


def _gravata(p, cor):
    """Gravata na frente do peito, dentro do contorno do corpo."""
    p.save()
    topo = BODY_H / 2 - 24
    escura = cor.darker(140)
    p.setPen(QPen(escura, 1.2))
    p.setBrush(cor)
    p.drawPolygon(
        QPolygonF([QPointF(-4, topo), QPointF(4, topo), QPointF(3.5, topo + 6), QPointF(-3.5, topo + 6)])
    )
    p.drawPolygon(
        QPolygonF(
            [
                QPointF(-3, topo + 5),
                QPointF(3, topo + 5),
                QPointF(5.5, topo + 17),
                QPointF(0, topo + 21),
                QPointF(-5.5, topo + 17),
            ]
        )
    )
    p.setPen(QPen(escura, 1.5))
    p.drawLine(QPointF(-4, topo + 10), QPointF(4, topo + 8))
    p.restore()


def _headset(p, cor, base_escura=SHELL):
    """Headset gamer para o modo clássico."""
    p.save()
    p.setPen(QPen(QColor(base_escura).lighter(150), 5, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(-BODY_W / 2 - 4, -BODY_H / 2 - 10, BODY_W + 8, 50), 0, 180 * 16)
    p.setPen(QPen(cor, 2))
    p.setBrush(QColor(base_escura))
    for s in (-1, 1):
        p.drawRoundedRect(QRectF(s * (BODY_W / 2 + 2) - 7, -14, 14, 28), 5, 5)
    p.restore()


def _chifrinhos(p, cor):
    """Chifrinhos de pestinha no topo."""
    p.save()
    p.setPen(QPen(QColor(cor).darker(140), 1.5))
    p.setBrush(cor)
    for s in (-1, 1):
        p.drawPolygon(
            QPolygonF(
                [
                    QPointF(s * 26, -BODY_H / 2),
                    QPointF(s * 38, -BODY_H / 2 - 16),
                    QPointF(s * 16, -BODY_H / 2),
                ]
            )
        )
    p.restore()


def _bone(p, cor):
    """Boné simples no topo."""
    p.save()
    p.setPen(Qt.NoPen)
    p.setBrush(cor)
    p.drawRoundedRect(QRectF(-38, -BODY_H / 2 - 10, 76, 14), 6, 6)
    p.drawRoundedRect(QRectF(-20, -BODY_H / 2 - 2, 68, 6), 3, 3)
    p.restore()


def _gorro_natal(p, cor):
    """Gorro de Natal."""
    p.save()
    p.setPen(Qt.NoPen)
    p.setBrush(cor)
    p.drawPolygon(
        QPolygonF([QPointF(-34, -BODY_H / 2), QPointF(34, -BODY_H / 2), QPointF(22, -BODY_H / 2 - 24)])
    )
    p.setBrush(QColor("#ffffff"))
    p.drawRoundedRect(QRectF(-38, -BODY_H / 2 - 4, 76, 8), 4, 4)
    p.drawEllipse(QPointF(24, -BODY_H / 2 - 24), 6, 6)
    p.restore()


def _chapeu_festa(p, cor):
    """Chapéu de aniversário."""
    p.save()
    p.setPen(Qt.NoPen)
    p.setBrush(cor)
    p.drawPolygon(
        QPolygonF([QPointF(-20, -BODY_H / 2), QPointF(20, -BODY_H / 2), QPointF(0, -BODY_H / 2 - 24)])
    )
    p.setBrush(QColor("#ff2a85"))
    p.drawEllipse(QPointF(0, -BODY_H / 2 - 25), 5, 5)
    p.restore()


_DESENHAR_ACESSORIO = {
    "oculos": _oculos,
    "gravata": _gravata,
    "headset": _headset,
    "chifrinhos": _chifrinhos,
    "bone": _bone,
    "gorro_natal": _gorro_natal,
    "chapeu_festa": _chapeu_festa,
}


def draw_zzz(p, cx, cy, now, cor=EYE):
    """Zs subindo do canto de cima do corpo, crescendo, balançando e sumindo."""
    for i in range(ZZZ_COUNT):
        t = ((now / ZZZ_PERIOD) + i / ZZZ_COUNT) % 1.0
        x = cx + BODY_W * 0.32 + 34 * t + 5 * math.sin(t * math.tau * 1.5)
        y = cy - BODY_H * 0.42 - 44 * t
        size = 8 + 9 * t
        alpha = int(255 * min(1.0, t * 5) * (1.0 - t) ** 0.6)
        color = QColor(cor)
        color.setAlpha(alpha)
        p.save()
        p.translate(x, y)
        p.rotate(-12 + 10 * math.sin(t * math.tau))
        p.setPen(color)
        p.setFont(QFont("Consolas", int(size), QFont.Bold))
        p.drawText(QRectF(-20, -20, 40, 40), Qt.AlignCenter, "Z")
        p.restore()
