"""
DESENHO DO ROSTO - só o que se desenha do pet: corpo/moldura, olhos, brilho, acessórios e os Zzz.

Suporta dois estilos visuais configuráveis em `aparencia.estilo` no `<pet>.json`:
- `"tv"` (padrão clássico): telinha arredondada com olhos expressivos.
- `"anime_pixel"`: garota de anime chibi em pixel art (cabelo em camadas, bochechas, olhos de anime
  que seguem o cursor, boquinha expressiva por emoção e acessórios como headset gamer e chifrinhos).
"""

import math
import re
from dataclasses import dataclass, field

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF

from ..ajustes import ZZZ_PERIODO as ZZZ_PERIOD, ZZZ_QUANTIDADE as ZZZ_COUNT

BODY_W, BODY_H = 120, 90
FRAME = QColor("#63e56f")
SHELL = QColor("#101512")
SCREEN = QColor("#171e19")
EYE = QColor("#3ee877")
SHINE = QColor("#c8ffd8")

ESTILOS_VALIDOS = ("tv", "anime_pixel")
ACESSORIOS = ("oculos", "gravata", "headset", "chifrinhos", "bone", "gorro_natal", "chapeu_festa")
COR_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
COR_PADRAO_ACESSORIO = {
    "oculos": "#e8e8e8",
    "gravata": "#b3261e",
    "headset": "#00f0ff",
    "chifrinhos": "#ff2a85",
    "bone": "#7c4dff",
    "gorro_natal": "#d62828",
    "chapeu_festa": "#ffbe0b",
}


@dataclass(frozen=True)
class Aparencia:
    """Cores do corpo, estilo visual e acessórios de um pet. O padrão é o visual original."""

    moldura: QColor = field(default_factory=lambda: QColor(FRAME))
    casca: QColor = field(default_factory=lambda: QColor(SHELL))
    tela: QColor = field(default_factory=lambda: QColor(SCREEN))
    olho: QColor = field(default_factory=lambda: QColor(EYE))
    brilho: QColor = field(default_factory=lambda: QColor(SHINE))
    acessorios: tuple = ()  # ((nome, QColor), ...) na ordem em que são desenhados
    estilo: str = "tv"
    suando: bool = False
    apertado: bool = False


CAMPOS_DE_COR = ("moldura", "casca", "tela", "olho", "brilho")


def aparencia_de(dados):
    """
    Monta a Aparencia a partir do "aparencia" do pet.json. Cor fora do formato #rrggbb e
    acessório desconhecido são ignorados (ficam com o padrão), como os outros campos do pet.
    """
    if not isinstance(dados, dict):
        return Aparencia()
    cores = {
        k: QColor(dados[k])
        for k in CAMPOS_DE_COR
        if isinstance(dados.get(k), str) and COR_HEX.match(dados[k])
    }
    estilo = dados.get("estilo") if dados.get("estilo") in ESTILOS_VALIDOS else "tv"
    pedidos = dados.get("acessorios")
    acessorios = []
    if isinstance(pedidos, dict):
        for nome in ACESSORIOS:  # ordem fixa
            if nome in pedidos:
                cor = pedidos[nome]
                cor = cor if isinstance(cor, str) and COR_HEX.match(cor) else COR_PADRAO_ACESSORIO[nome]
                acessorios.append((nome, QColor(cor)))
    return Aparencia(**cores, acessorios=tuple(acessorios), estilo=estilo)


PADRAO = Aparencia()


def lerp_shape(current, target, k):
    """Interpola duas formas de olho: `k` entre 0 (atual) e 1 (alvo), para a transição ser suave."""
    return {key: current[key] + (target[key] - current[key]) * k for key in target}


def draw_face(p, shape, gaze=(0.0, 0.0), blink=1.0, emotion="observando", carinho=False, aparencia=PADRAO):
    """Desenha o pet (estilo clássico 'tv' ou 'anime_pixel') com centro na origem do painter."""
    a = aparencia
    p.save()
    if getattr(a, "apertado", False):
        p.scale(0.84, 1.08)  # RAM cheia: espremida horizontalmente
    if a.estilo == "anime_pixel":
        _draw_anime_pixel(p, shape, gaze, blink, emotion, carinho, a)
    else:
        _draw_tv(p, shape, gaze, blink, emotion, carinho, a)
    if getattr(a, "suando", False):
        _desenhar_suor(p)
    p.restore()


def _draw_tv(p, shape, gaze, blink, emotion, carinho, a):
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


def _px(p, gx, gy, gw, gh, cor, grid=4):
    """Desenha um bloco retangular alinhado na grade de pixel art (cada unidade = `grid` px)."""
    p.fillRect(QRectF(gx * grid, gy * grid, gw * grid, gh * grid), cor)


def _draw_anime_pixel(p, shape, gaze, blink, emotion, carinho, a):
    """
    Garota de anime chibi em pixel art (grade 4 px).
    - `a.moldura`: cor principal do cabelo
    - `a.casca`: roupa / contorno escuro
    - `a.tela`: detalhe secundário da roupa / sombra
    - `a.olho`: íris dos olhos de anime
    - `a.brilho`: brilho dos olhos e mechas de luz no cabelo
    """
    p.save()
    p.setRenderHint(QPainter.Antialiasing, False)
    p.setPen(Qt.NoPen)

    cabelo = a.moldura
    cabelo_escuro = QColor(cabelo).darker(145)
    cabelo_luz = a.brilho
    pele = QColor("#ffe3d3")
    pele_sombra = QColor("#f3bfa8")
    blush = QColor("#ff7aa2")
    roupa = a.casca
    roupa_detalhe = a.tela

    # 1. Cabelo de trás e maria-chiquinhas (twintails) volumosas
    _px(p, -11, -9, 22, 16, cabelo_escuro)
    # Twintails laterais
    for s in (-1, 1):
        base_x = -15 if s < 0 else 11
        _px(p, base_x, -6, 4, 14, cabelo)
        _px(p, base_x + (0 if s < 0 else 1), -4, 3, 13, cabelo_escuro)
        _px(p, base_x + (1 if s < 0 else 0), -5, 2, 3, cabelo_luz)

    # 2. Corpinho / ombros chibi (dentro de BODY_H: até y = +11 na grade = +44 px)
    _px(p, -7, 6, 14, 5, roupa)
    _px(p, -5, 6, 10, 4, roupa_detalhe)
    # Gola / gravatinha ou detalhe neon no peito
    _px(p, -2, 6, 4, 2, pele_sombra)
    _px(p, -1, 8, 2, 3, a.olho)

    for nome, cor in a.acessorios:
        if nome == "gravata":
            _px(p, -1, 7, 2, 4, cor)

    # 3. Rosto (cabeça chibi arredondada em pixel art)
    _px(p, -9, -7, 18, 12, pele)
    _px(p, -8, -8, 16, 14, pele)
    _px(p, -7, 5, 14, 1, pele_sombra)  # sombra do queixo

    # 4. Topo do cabelo e franja (hime cut + franja em M)
    _px(p, -10, -11, 20, 4, cabelo)
    _px(p, -9, -12, 18, 2, cabelo)
    _px(p, -6, -10, 12, 1, cabelo_luz)  # halo de brilho no cabelo
    # Franja na testa
    _px(p, -9, -7, 3, 4, cabelo)
    _px(p, -5, -7, 3, 3, cabelo)
    _px(p, -1, -7, 3, 4, cabelo)
    _px(p, 3, -7, 3, 3, cabelo)
    _px(p, 6, -7, 3, 4, cabelo)
    # Mechas laterais emoldurando o rosto (hime cut)
    _px(p, -10, -7, 2, 13, cabelo)
    _px(p, 8, -7, 2, 13, cabelo)
    _px(p, -10, 2, 2, 4, cabelo_escuro)
    _px(p, 8, 2, 2, 4, cabelo_escuro)

    # 5. Bochechas coradas (blush)
    if carinho or emotion in ("feliz", "contente", "bravo", "dramatico"):
        _px(p, -7, 1, 2, 1, blush)
        _px(p, 5, 1, 2, 1, blush)

    # 6. Olhos de anime em pixel art (seguem o gaze)
    gx_px = int(round(max(-1.0, min(1.0, gaze[0]))))
    gy_px = int(round(max(-1.0, min(1.0, gaze[1]))))
    fechado = blink <= 0.35 or emotion == "dormindo"

    if carinho:
        # Olhinhos ^ ^ felizes em pixel art
        for ox in (-6, 3):
            _px(p, ox, -2, 1, 1, a.olho)
            _px(p, ox + 1, -3, 1, 1, a.olho)
            _px(p, ox + 2, -2, 1, 1, a.olho)
    elif fechado:
        # Olhinhos fechados com cílios
        for ox in (-6, 3):
            _px(p, ox, -1, 3, 1, cabelo_escuro)
            _px(p, ox, 0, 3, 1, a.olho)
    else:
        for side, ox in ((-1, -6), (1, 3)):
            # Esclera branca + cílio superior grosso
            _px(p, ox, -3, 3, 4, QColor("#ffffff"))
            _px(p, ox, -4, 3, 1, QColor("#1a1026"))
            # Íris colorida (move com o olhar)
            ix = max(ox, min(ox + 1, ox + (1 if gx_px >= 0 else 0)))
            iy = -3 + max(0, min(1, gy_px + 1))
            _px(p, ix, iy, 2, 3, a.olho)
            _px(p, ix, iy + 1, 2, 1, QColor(a.olho).darker(135))
            # Brilho de anime no canto superior da íris
            _px(p, ix, iy, 1, 1, a.brilho)

            # Sobrancelhas expressivas conforme a emoção
            if emotion == "bravo":
                # Sobrancelha franzida em diagonal
                _px(p, ox + (2 if side < 0 else 0), -4, 1, 1, cabelo_escuro)
                _px(p, ox + 1, -5, 1, 1, cabelo_escuro)
            elif emotion in ("triste", "dramatico"):
                _px(p, ox + (0 if side < 0 else 2), -4, 1, 1, cabelo_escuro)
                _px(p, ox + 1, -5, 1, 1, cabelo_escuro)
                # Lagriminha pixelada no canto do olho
                _px(p, ox + (0 if side < 0 else 2), 1, 1, 1, QColor("#4cc9f0"))

    # Sinal de raiva de anime (veia saltando) na testa quando brava
    if emotion == "bravo":
        veia = QColor("#ff2a6d")
        _px(p, 5, -9, 1, 2, veia)
        _px(p, 4, -8, 3, 1, veia)

    # 7. Boquinha de anime conforme a emoção
    boca_cor = QColor("#d94b68")
    if carinho or emotion == "feliz":
        # Sorriso aberto fofo (:D / :3)
        _px(p, -1, 2, 2, 2, boca_cor)
        _px(p, -2, 2, 1, 1, boca_cor)
        _px(p, 1, 2, 1, 1, boca_cor)
    elif emotion == "contente":
        _px(p, -1, 3, 2, 1, boca_cor)
        _px(p, 1, 2, 1, 1, boca_cor)
    elif emotion in ("curioso", "assustado"):
        # Boquinha 'o' surpresa
        _px(p, -1, 2, 2, 2, boca_cor)
    elif emotion == "bravo":
        # Boquinha franzida de rage
        _px(p, -2, 3, 1, 1, boca_cor)
        _px(p, -1, 2, 2, 1, boca_cor)
        _px(p, 1, 3, 1, 1, boca_cor)
    elif emotion in ("triste", "dramatico"):
        _px(p, -1, 2, 2, 1, boca_cor)
        _px(p, -2, 3, 1, 1, boca_cor)
        _px(p, 1, 3, 1, 1, boca_cor)
    else:
        _px(p, -1, 3, 2, 1, boca_cor)

    # 8. Acessórios em pixel art
    for nome, cor in a.acessorios:
        if nome == "chifrinhos":
            _chifrinhos_pixel(p, cor)
        elif nome == "headset":
            _headset_pixel(p, cor, a.casca)
        elif nome == "oculos":
            _oculos_pixel(p, cor)
        elif nome == "bone":
            _bone_pixel(p, cor)
        elif nome == "gorro_natal":
            _gorro_natal_pixel(p, cor)
        elif nome == "chapeu_festa":
            _chapeu_festa_pixel(p, cor)

    p.restore()


def _chifrinhos_pixel(p, cor):
    """Dois chifrinhos de pestinha curvados no topo da cabeça."""
    escuro = QColor(cor).darker(135)
    for s in (-1, 1):
        bx = -7 if s < 0 else 5
        _px(p, bx, -13, 2, 2, escuro)
        _px(p, bx + (0 if s < 0 else 1), -15, 1, 2, cor)
        _px(p, bx + (1 if s < 0 else 0), -14, 1, 2, cor)


def _headset_pixel(p, cor, base_escura):
    """Headset gamer com tiara, conchas laterais com LED neon e microfone."""
    carcaca = QColor(base_escura).lighter(130)
    # Tiara superior
    _px(p, -9, -12, 18, 1, carcaca)
    _px(p, -11, -10, 2, 3, carcaca)
    _px(p, 9, -10, 2, 3, carcaca)
    # Conchas acústicas nas laterais com anel de LED `cor`
    for bx in (-12, 9):
        _px(p, bx, -6, 3, 6, carcaca)
        _px(p, bx + 1, -5, 1, 4, cor)
    # haste do microfone na esquerda
    _px(p, -10, 0, 2, 1, carcaca)
    _px(p, -8, 1, 2, 1, cor)


def _oculos_pixel(p, cor):
    """Óculos estilizados em pixel art."""
    for ox in (-7, 2):
        _px(p, ox, -4, 5, 1, cor)
        _px(p, ox, 0, 5, 1, cor)
        _px(p, ox, -4, 1, 5, cor)
        _px(p, ox + 4, -4, 1, 5, cor)
    _px(p, -2, -3, 4, 1, cor)


def _bone_pixel(p, cor):
    """Boné em pixel art no topo da cabeça."""
    _px(p, -9, -13, 18, 3, cor)
    _px(p, -6, -10, 16, 1, QColor(cor).darker(130))


def _gorro_natal_pixel(p, cor):
    """Gorro de Natal em pixel art (vermelho com borda e pompom brancos)."""
    branco = QColor("#ffffff")
    _px(p, -9, -12, 18, 2, branco)
    _px(p, -7, -15, 14, 3, cor)
    _px(p, -4, -17, 10, 2, cor)
    _px(p, 6, -16, 3, 3, branco)


def _chapeu_festa_pixel(p, cor):
    """Chapéu de aniversário em cone com pompom."""
    _px(p, -4, -14, 8, 2, cor)
    _px(p, -2, -16, 4, 2, cor)
    _px(p, -1, -18, 2, 2, QColor("#ff2a85"))


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

        if blink > 0.5 and h >= 8:  # olho fechado não tem brilho
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


def _headset(p, cor, base_escura):
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


def _desenhar_suor(p):
    """Gotinhas de suor azuis quando a CPU do PC está alta."""
    p.save()
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#4cc9f0"))
    p.drawEllipse(QPointF(42, -24), 4, 6)
    p.drawEllipse(QPointF(48, -12), 3, 5)
    p.restore()


def draw_zzz(p, cx, cy, now, cor=EYE):
    """Zs subindo do canto de cima do corpo, crescendo, balançando e sumindo."""
    for i in range(ZZZ_COUNT):
        t = ((now / ZZZ_PERIOD) + i / ZZZ_COUNT) % 1.0  # 0 nasce ... 1 some
        x = cx + BODY_W * 0.32 + 34 * t + 5 * math.sin(t * math.tau * 1.5)
        y = cy - BODY_H * 0.42 - 44 * t  # sobe até ~12 px do topo da janela
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
