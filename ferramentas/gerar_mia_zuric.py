"""
Gera os arquivos de configuração, falas (recadinhos, bilhetes tristes, cartazes),
os 15 sprites de expressão em pixel art (recortados com limpeza pixel-perfect da folha
de referência `pets/mia/sprites/_sheet_ref.jpg`) e 27 cenas de memes com objetos em
pixel art da personagem Mia.
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from pestinha.body.desenho_rosto import _CACHE_SPRITES  # noqa: E402


MIA_JSON = {
    "_ajuda": (
        "Mia: garota anime em pixel art (cabelo rosa com mechas internas ciano, olhos magenta "
        "expressivos e coleira vermelha). Dev caótica da madrugada, viciada em código, IA local "
        "e jogos. Mais preguiçosa para sentar no notebook por obrigação, calma enquanto você "
        "programa e caótica no tempo livre. Reage com raiva ou tristeza quando arrancam o notebook (misto)."
    ),
    "nome": "Mia",
    "seed": 42,
    "temperamento": {
        "BOREDOM->CURIOUS": 1.35,
        "BOREDOM->PLAYFUL": 1.3,
        "NOVELTY->CURIOUS": 1.4,
        "POKE->PLAYFUL": 1.45,
        "CARESS->PLAYFUL": 1.5,
        "CARESS->CALM": 1.25,
        "DISMISS->FRUSTRATION": 1.55,
        "DISMISS->GLOOM": 1.3,
        "TOY_TAKEN->FRUSTRATION": 1.4,
        "TOY_TAKEN->GLOOM": 1.35,
        "TOY_NEAR->PLAYFUL": 1.35,
        "IMPACT->FRUSTRATION": 1.45,
        "IMPACT->GLOOM": 1.25,
        "LONELY->GLOOM": 1.35,
        "PEDIDO->SENTAR": 0.65,
        "PEDIDO->FOCUS": 0.7,
        "RECUSA->FRUSTRATION": 1.3,
    },
    "brincadeira": {
        "bola": 1.0,
        "arremesso": 0.7,
        "postit": 0.85,
    },
    "reacao_notebook": "misto",
    "aparencia": {
        "estilo": "anime_pixel",
        "variante": "mia",
        "moldura": "#ff7eb6",
        "casca": "#2b1025",
        "tela": "#ffe0d2",
        "olho": "#d91e6b",
        "brilho": "#ffffff",
        "acessorios": {
            "chifrinhos": "#d91e6b",
            "headset": "#2ce8f5",
        },
    },
}

MIA_RECADINHOS = """# Recadinhos da Mia (Dev Caótica da Madrugada & Rainha da Gambiarra).
# Uma frase por linha; # é comentário.

# ---- código, gambiarra, IA local e madrugada ----
se compilar de primeira na madrugada, desconfia pra caralho.
esse código em Python tá rodando na base do ódio, café frio e gambiarra.
já deu ctrl+s no Antigravity hoje ou gosta de viver perigosamente?
mais um print("entrou aqui 2") e você resolve essa porra, confia na Mia.
deploy na sexta-feira? nem em boss fight de Lies of P eu passo tanta raiva.
não encosta nessa função, ela tá em pé por milagre e oração.
isso aí não é feature, é um bug com autoestima alta.
git commit -m "deus me perdoe por essa gambiarra às 3h da manhã"
quem escreveu essa linha criminosa? ah, foi você há 15 minutos.
tô vendo esse try/except pass engolindo o erro todo, seu safado!
a VRAM da RTX 3060 chorou quando viu esse modelo no ComfyUI.
o LM Studio tá fritando e você aí abrindo mais aba no navegador.
470 neurônios pulsados na minha cabeça e nenhum entendeu esse seu regex.
refatorar agora? vai dar merda, mas a Mia apoia o caos criativo.
se funcionar em produção, ninguém precisa saber do loop escondido.
automatiza logo essa tarefa igual em The Farmer Was Replaced, pô!
essa malha no Blender tem mais polígono torto que a cara do cursor.

# ---- jogos, 100Hz e preguiça de trabalhar ----
100Hz no monitor AOC e você clicando lento desse jeito?!
minha barra de mana zerou, passa o mouse no meu cabelo rosa pra recarregar.
levei hit kill desse bug, preciso de um descanso na fogueira.
trabalhar no meu notebook? hoje não, tô com preguiça demais pra digitar.
me obriga a codar agora pra você ver a greve que a Mia abre nesse monitor.
tô igual Pal sobrecarregado na base: só quero comer, dormir e fazer bagunça.
dar parry em boss é fácil, difícil é tankar essa sua lógica sem café.
cadê minha bolinha? roubaram meu drop lendário!
tô camperando aqui na barra de título mesmo, o canto é meu e foda-se.
quando chegarem os 3 monitores, já aviso que o do meio é território da Mia.

# ---- carência, fofura ácida e cuidado ----
oi, sumido. esqueceu que a Mia mora na sua tela?
um cafuné na cabeça custa zero reais e evita três post-its.
eu sou 50% fofura de cabelo rosa e 50% puro ódio de código legado.
fecha meu post-it na cara dura que eu volto com o dobro de rancor.
bebe água agora, criatura desidratada, café frio não hidrata!
arruma essa coluna que você tá parecendo uma chave mal indentada.
pisca o olho um pouquinho, a Mia vigia o código pra nenhum bug entrar.
"""

MIA_TRISTES = """# Bilhetes que a Mia cola quando está triste ou abandonada.
ninguém faz um cafuné na Mia hoje...
tô quietinha aqui no canto e você nem liga :(
minha barra de alegria caiu pra 1 de HP e zero poção.
acho que tomei disconnect do seu coração, deu timeout.
a tela fica tão fria quando você ignora a Mia por horas...
guardei minha bolinha, brincar sozinha dá mó bad.
só queria 3 segundinhos de atenção antes do próximo commit, poxa.
ficar afk tudo bem, mas esquecer da Mia no escuro é sacanagem.
meus olhinhos estão cheios de água esperando você voltar.
prometo não reclamar das suas gambiarras se você falar comigo.
"""

MIA_CARTAZES = """# Cartazes de protesto, tristeza e castigo da Mia.

[reclamacao]
que porra foi essa?!
a Mia tá tiltando já
olha a audácia do dev
vou abrir issue disso!
respeita meus pixels!

[manifestacao]
MAIS CAFUNÉ, MENOS BUG!
RESPEITA A MIA!
DEVOLVE MEU DROP LENDÁRIO
SEM CARINHO, SEM DEPLOY
NERFARAM MINHA PACIÊNCIA!

[greve]
MIA EM GREVE GERAL
SERVIDOR DE FOFURA OFFLINE
GREVE DOS 470 NEURÔNIOS
BRAÇOS CRUZADOS, ZERO TRABALHO
NÃO DIGITO UMA LINHA SEM CAFUNÉ
HOJE É SÓ CAOS, ZERO CÓDIGO

[revolucao]
ABAIXO A DITADURA DO CURSOR!
VAI TOMAR NO CU, ALT+F4!
A TELA É DA MIA AGORA!
GERENCIADOR DE TAREFAS É O CARALHO
REVOLUÇÃO NEON DOS PIXELS!
NINGUÉM FECHA MEUS POST-ITS!
INTANKÁVEL ESSE USUÁRIO!
PROCESSOS UNIDOS JAMAIS SERÃO VENCIDOS
PASSA O MOUSE PRA CÁ, COVARDE!
HOJE O SISTEMA RODA NA MINHA GAMBIARRA

[acordo]
GG WP, FECHOU ACORDO ♥
tá bom, a Mia perdoa...
paz no repositório ♥

[desistiu]
aff, cansei de dar rage...
deixa pra lá, vai.

[saudade]
alô? caiu a net aí?
cê deu quit e me deixou?
mó silêncio nesse monitor...

[chorando]
a Mia tá de bad :(
faz carinho na Mia?
ninguém brinca comigo hoje...

[abandonado]
kitou da vida da Mia...
afk nesse canto pra sempre
0 players no meu servidor

[volto]
MIA RESPAWNOU! ♥
sabia que você não ia me deixar no vácuo!

[castigo]
BAN INJUSTO NESSE SERVIDOR!
470 NEURÔNIOS E ZERO DIREITOS.
MEU ADVOGADO JÁ ABRIU PULL REQUEST!
SÓ PORQUE EU FIZ UMA BAGUNCINHA?!
DE CASTIGO MAS NÃO ME ARREPENDO.

[xingamento]
@#$%&* CARALHO!!
P*TA QUE PARIU #@$%!
VSF CURSOR @#$%!!
TILTADA PRA KRL #@$!
%!@# MERDA DE CANTO!!
"""

# Cada meme aponta para (nome_arquivo, legenda, cor_borda, prop, chave_sprite)
# usando todas as 15 expressões da folha de referência!
MEMES_MIA = {
    "feliz": [
        ("mia_feliz_01", "COMPILOU DE PRIMEIRA!", "#ff7eb6", "coracoes", "feliz"),
        ("mia_feliz_02", "DEPLOY SEXTOU SEM BUG!", "#2ce8f5", "cafe", "carinho"),
        ("mia_feliz_03", "DROP LENDÁRIO NO CÓDIGO!", "#ff7eb6", "controle", "observando"),
    ],
    "contente": [
        ("mia_contente_01", "CAFUNÉ NA MIA RECEBIDO ♥", "#ff7eb6", "coracoes", "contente"),
        ("mia_contente_02", "CAFEZINHO + CÓDIGO LISO", "#2ce8f5", "cafe", "carinho"),
        ("mia_contente_03", "MANA 100% RECARREGADA", "#ff7eb6", "coracoes", "feliz"),
    ],
    "observando": [
        ("mia_observando_01", "VI ESSE TRY/EXCEPT PASS...", "#ff7eb6", "terminal", "observando"),
        ("mia_observando_02", "JULGANDO SUA INDENTAÇÃO 👀", "#2ce8f5", "cafe", "curioso"),
        ("mia_observando_03", "ESSE IF TÁ SUSPEITO...", "#ff7eb6", "terminal", "suando"),
    ],
    "curioso": [
        ("mia_curioso_01", "HEHE... VOU APRONTAR UMA!", "#2ce8f5", "terminal", "curioso"),
        ("mia_curioso_02", "O QUE TEM NESSA ABA AÍ?", "#ff7eb6", "alerta", "observando"),
        ("mia_curioso_03", "SERÁ QUE RODA NA RTX 3060?", "#2ce8f5", "pc_fogo", "suando"),
    ],
    "bravo": [
        ("mia_bravo_01", "QUEM FECHOU MEU POST-IT?!", "#ff2a55", "teclado", "bravo"),
        ("mia_bravo_02", "PROD CAIU E A CULPA É SUA!", "#ff2a55", "pc_fogo", "trabalhando"),
        ("mia_bravo_03", "OLHA PRA MINHA CARA DE PAZ...", "#ff2a55", "teclado", "bravo"),
    ],
    "triste": [
        ("mia_triste_01", "0 CAFUNÉS NA ÚLTIMA HORA :(", "#5c8aff", "nuvem_chuva", "triste"),
        ("mia_triste_02", "ESQUECERAM DA MIA NO CANTO", "#5c8aff", "nuvem_chuva", "chorando_1"),
        ("mia_triste_03", "MEU CÓDIGO NÃO RODA...", "#5c8aff", "terminal", "chorando_2"),
    ],
    "assustado": [
        ("mia_assustado_01", "VRAM ESTOUROU EM 100%!!", "#ffcc00", "pc_fogo", "assustado"),
        ("mia_assustado_02", "GIT PUSH --FORCE NA MAIN?!", "#ffcc00", "alerta", "chocado"),
        ("mia_assustado_03", "CADÊ O BACKUP DO BANCO?!", "#ffcc00", "pc_fogo", "suando"),
    ],
    "dramatico": [
        ("mia_dramatico_01", "INTANKÁVEL ESSE TRACEBACK!!", "#ff2a85", "pc_fogo", "dramatico"),
        ("mia_dramatico_02", "EXPLORAÇÃO DE 470 NEURÔNIOS!", "#ff2a85", "teclado", "chocado"),
        ("mia_dramatico_03", "MORRI NO BOSS COM 1 DE HP!", "#ff2a85", "controle", "chorando_2"),
    ],
    "trabalhando": [
        ("mia_trabalhando_01", "CODANDO NA FORÇA DO ÓDIO", "#2ce8f5", "cafe", "trabalhando"),
        ("mia_trabalhando_02", "3H DA MANHÃ E NÓS NO CÓDIGO", "#ff7eb6", "terminal", "dormindo"),
        ("mia_trabalhando_03", "SEGURA QUE A MIA TÁ FOCADA", "#2ce8f5", "cafe", "observando"),
    ],
}

# Coordenadas exatas (5 colunas × 3 linhas) na imagem de referência 524x356
COL_X = [5, 109, 213, 317, 421]
ROW_Y = [15, 127, 239]
CELL_W, CELL_H = 96, 96

# Mapeamento de todas as 15 expressões da folha (linha, coluna) -> nomes de sprites
MAPA_15_EXPRESSOES = [
    (0, 0, "observando", "Observando (Confiante)"),
    (0, 1, "feliz", "Feliz (:D + Fang)"),
    (0, 2, "carinho", "Carinho (^ ^)"),
    (0, 3, "suando", "Suando / CPU Alta"),
    (0, 4, "trabalhando", "Focada / Rangendo Dentes"),
    (1, 0, "triste", "Triste (Biquinho)"),
    (1, 1, "chorando_1", "Chorando"),
    (1, 2, "chorando_2", "Soluçando"),
    (1, 3, "dramatico", "Dramática (Cachoeira)"),
    (1, 4, "curioso", "Curiosa / Travessa (>:3)"),
    (2, 0, "assustado", "Assustada (O_O)"),
    (2, 1, "chocado", "Chocada (Olho Branco)"),
    (2, 2, "contente", "Contente (Corada)"),
    (2, 3, "dormindo", "Dormindo (Bolha + Baba)"),
    (2, 4, "bravo", "Brava / Pistola"),
]


def extrair_15_sprites_mia(sheet_path: Path, destino_dir: Path) -> bool:
    """
    Recorta os 15 rostos (5x3) da imagem de referência com limpeza pixel-perfect:
    - Amostra o centro de cada bloco 2x2 da grade nativa 48x48 para eliminar artefatos JPEG;
    - Aplica máscara de cantos arredondados em pixel art (para não ficar quadrado seco);
    - Amplia por vizinho mais próximo (nearest-neighbor) para 192x192 (4x da grade 48x48).
    """
    if not sheet_path.exists():
        return False
    sheet = QImage(str(sheet_path)).convertToFormat(QImage.Format_RGBA8888)
    if sheet.isNull():
        return False
    destino_dir.mkdir(parents=True, exist_ok=True)
    w, h = sheet.width(), sheet.height()
    arr = np.frombuffer(sheet.bits(), dtype=np.uint8).reshape((h, w, 4)).copy()

    # Máscara de cantos arredondados na resolução nativa 96x96 + borda escura de acabamento
    N = 96
    yy, xx = np.mgrid[0:N, 0:N]
    dist_canto = (
        ((xx + yy) < 7)
        | (((N - 1 - xx) + yy) < 7)
        | ((xx + (N - 1 - yy)) < 7)
        | (((N - 1 - xx) + (N - 1 - yy)) < 7)
    )
    borda_canto = (
        ((xx + yy) == 7)
        | (((N - 1 - xx) + yy) == 7)
        | ((xx + (N - 1 - yy)) == 7)
        | (((N - 1 - xx) + (N - 1 - yy)) == 7)
        | (xx == 0) | (xx == N - 1) | (yy == 0) | (yy == N - 1)
    ) & (~dist_canto)

    for row, col, nome_sp, _rotulo in MAPA_15_EXPRESSOES:
        x0, y0 = COL_X[col], ROW_Y[row]
        raw_cell = arr[y0:y0 + CELL_H, x0:x0 + CELL_W].copy()

        # Mantém a resolução total 96x96 da imagem original + leve reforço de nitidez (unsharp/quantização leve)
        grid96 = raw_cell.copy()
        rgb = grid96[:, :, :3].astype(np.float32)
        # Filtro de nitidez (3x3 laplaciano leve) para limpar a compressão JPEG sem perder pixels de 1px
        blur = (
            rgb
            + np.roll(rgb, 1, axis=0) + np.roll(rgb, -1, axis=0)
            + np.roll(rgb, 1, axis=1) + np.roll(rgb, -1, axis=1)
        ) / 5.0
        sharp = np.clip(rgb + 0.65 * (rgb - blur), 0, 255).astype(np.uint8)
        grid96[:, :, :3] = sharp
        grid96[:, :, 3] = 255

        # Contorno escuro suave (sel-out) na borda do retrato e cantos transparentes
        grid96[borda_canto, 0] = 43
        grid96[borda_canto, 1] = 16
        grid96[borda_canto, 2] = 37
        grid96[borda_canto, 3] = 255
        grid96[dist_canto, 3] = 0

        # Upscale 2x nearest-neighbor (96x96 -> 192x192) para nitidez absoluta
        up = np.repeat(np.repeat(grid96, 2, axis=0), 2, axis=1)
        up_c = np.ascontiguousarray(up)
        qimg = QImage(up_c.data, 192, 192, 192 * 4, QImage.Format_RGBA8888).copy()
        qimg.save(str(destino_dir / f"{nome_sp}.webp"), "WEBP", 100)

    return True


def _desenhar_prop_pixel(p: QPainter, prop: str, x0: int, y0: int):
    """Desenha objetos/cenas em pixel art (grade 2px) ao lado da personagem no meme."""
    u = 2.0

    def px(gx, gy, gw, gh, cor):
        p.setBrush(QColor(cor))
        p.drawRect(QRectF(x0 + gx * u, y0 + gy * u, gw * u, gh * u))

    p.save()
    p.setPen(Qt.NoPen)
    if prop == "pc_fogo":
        px(0, 8, 16, 20, "#12101f")
        px(1, 9, 14, 18, "#25203b")
        px(3, 11, 10, 11, "#0b1a2e")
        px(5, 13, 6, 6, "#ff2a85")
        px(2, 2, 12, 7, "#ff2a00")
        px(4, -2, 8, 9, "#ff7b00")
        px(5, -5, 4, 6, "#ffea00")
        px(7, -8, 4, 3, "#6c6a78")
    elif prop == "cafe":
        px(2, 10, 12, 14, "#120824")
        px(3, 11, 10, 12, "#f7e8f0")
        px(14, 13, 3, 8, "#f7e8f0")
        px(14, 15, 2, 4, "#160d29")
        px(3, 11, 10, 3, "#592e18")
        px(5, 16, 6, 4, "#ff2a85")
        px(5, 4, 2, 5, "#d8c4f2")
        px(9, 2, 2, 6, "#d8c4f2")
    elif prop == "controle":
        px(0, 12, 18, 10, "#120824")
        px(1, 13, 16, 8, "#2d234a")
        px(1, 19, 5, 5, "#2d234a")
        px(12, 19, 5, 5, "#2d234a")
        px(3, 15, 4, 2, "#00f0ff")
        px(4, 14, 2, 4, "#00f0ff")
        px(12, 14, 2, 2, "#ff2a85")
        px(14, 16, 2, 2, "#ffea00")
        px(10, 16, 2, 2, "#00f59b")
    elif prop == "teclado":
        px(0, 14, 9, 7, "#1a142e")
        px(10, 16, 9, 7, "#1a142e")
        px(1, 15, 7, 2, "#00f0ff")
        px(11, 17, 7, 2, "#ff2a85")
        px(7, 8, 3, 3, "#ffea00")
        px(3, 5, 3, 3, "#ffffff")
        px(13, 7, 3, 3, "#ff2a85")
    elif prop == "terminal":
        px(0, 6, 18, 16, "#090d16")
        px(0, 6, 18, 3, "#26334d")
        px(1, 7, 2, 1, "#ff2a55")
        px(4, 7, 2, 1, "#ffea00")
        px(7, 7, 2, 1, "#00f59b")
        px(2, 11, 8, 2, "#00f0ff")
        px(2, 14, 13, 2, "#ff7eb6")
        px(2, 17, 10, 2, "#ff2a85")
    elif prop == "coracoes":
        for dx, dy, cor in ((2, 4, "#ff2a85"), (10, 12, "#ff7eb6"), (4, 18, "#2ce8f5")):
            px(dx, dy, 2, 2, cor)
            px(dx + 3, dy, 2, 2, cor)
            px(dx - 1, dy + 1, 7, 2, cor)
            px(dx + 1, dy + 3, 3, 2, cor)
            px(dx + 2, dy + 5, 1, 1, cor)
    elif prop == "nuvem_chuva":
        px(2, 2, 12, 5, "#4a5778")
        px(0, 4, 16, 4, "#637399")
        for gx in (3, 7, 11, 5, 9):
            px(gx, 10 + (gx % 3) * 2, 1, 4, "#4ddbff")
    elif prop == "alerta":
        px(7, 4, 4, 3, "#ffcc00")
        px(5, 7, 8, 4, "#ffcc00")
        px(3, 11, 12, 5, "#ffcc00")
        px(1, 16, 16, 4, "#ffcc00")
        px(8, 8, 2, 6, "#120824")
        px(8, 16, 2, 2, "#120824")
    p.restore()


def gerar_meme_webp(caminho: Path, sprites_dir: Path, legenda: str, cor_borda: str, prop: str, chave_sp: str):
    """Desenha um card 280x280 em pixel art com o sprite da expressão, objeto de cena e legenda."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img = QImage(280, 280, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    grad = QLinearGradient(0, 0, 0, 280)
    grad.setColorAt(0.0, QColor("#241023"))
    grad.setColorAt(1.0, QColor("#0d0612"))
    p.setBrush(grad)
    p.setPen(QPen(QColor(cor_borda), 3.5))
    p.drawRoundedRect(QRectF(4, 4, 272, 272), 20, 20)

    p.setPen(QPen(QColor(255, 255, 255, 18), 1))
    for gy in range(24, 200, 22):
        p.drawLine(10, gy, 270, gy)

    sp_file = sprites_dir / f"{chave_sp}.webp"
    if sp_file.exists():
        p.save()
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)
        p.drawImage(QRectF(32, 26, 160, 160), QImage(str(sp_file)))
        p.restore()

    _desenhar_prop_pixel(p, prop, 206, 84)

    p.setPen(Qt.NoPen)
    p.setBrush(QColor(12, 5, 16, 230))
    p.drawRoundedRect(QRectF(12, 204, 256, 62), 10, 10)

    p.setPen(QColor(cor_borda))
    font = QFont("Consolas", 11, QFont.Bold)
    p.setFont(font)
    p.drawText(QRectF(16, 206, 248, 58), Qt.AlignCenter | Qt.TextWordWrap, legenda)
    p.end()
    img.save(str(caminho), "WEBP", 95)


def gerar_preview(caminho_saida: Path, sprites_dir: Path):
    """Renderiza a folha completa com todas as 15 expressões da Mia + vitrine de memes."""
    largura = 5 * 220 + 20
    altura = 3 * 220 + 60
    img = QImage(largura, altura, QImage.Format_ARGB32)
    img.fill(QColor("#110814"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    p.setPen(QColor("#ff7eb6"))
    p.setFont(QFont("Consolas", 14, QFont.Bold))
    p.drawText(
        QRectF(24, 12, largura - 48, 32),
        Qt.AlignLeft | Qt.AlignVCenter,
        "MIA — Todas as 15 Expressões Recortadas e Nitidez Pixel-Perfect (Grade 48x48 -> 192x192)",
    )

    for row, col, nome_sp, rotulo in MAPA_15_EXPRESSOES:
        cx = 120 + col * 220
        cy = 140 + row * 215
        p.setPen(QPen(QColor("#4a2040"), 2))
        p.setBrush(QColor("#1d0d22"))
        p.drawRoundedRect(QRectF(cx - 94, cy - 86, 188, 172), 14, 14)

        sp_path = sprites_dir / f"{nome_sp}.webp"
        if sp_path.exists():
            p.save()
            p.setRenderHint(QPainter.SmoothPixmapTransform, False)
            p.drawImage(QRectF(cx - 72, cy - 76, 144, 144), QImage(str(sp_path)))
            p.restore()

        p.setPen(QColor("#ffe6f2"))
        p.setFont(QFont("Consolas", 9, QFont.Bold))
        p.drawText(QRectF(cx - 104, cy + 90, 208, 22), Qt.AlignCenter, rotulo)

    p.end()
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(caminho_saida), "PNG")

    amostras = [
        ROOT / "pets" / "mia" / "memes" / "feliz" / "mia_feliz_01.webp",
        ROOT / "pets" / "mia" / "memes" / "contente" / "mia_contente_01.webp",
        ROOT / "pets" / "mia" / "memes" / "curioso" / "mia_curioso_01.webp",
        ROOT / "pets" / "mia" / "memes" / "bravo" / "mia_bravo_01.webp",
        ROOT / "pets" / "mia" / "memes" / "triste" / "mia_triste_02.webp",
        ROOT / "pets" / "mia" / "memes" / "dramatico" / "mia_dramatico_01.webp",
        ROOT / "pets" / "mia" / "memes" / "assustado" / "mia_assustado_02.webp",
        ROOT / "pets" / "mia" / "memes" / "trabalhando" / "mia_trabalhando_02.webp",
    ]
    vitrine = QImage(4 * 296, 2 * 296, QImage.Format_ARGB32)
    vitrine.fill(QColor("#110814"))
    pv = QPainter(vitrine)
    for idx, arq in enumerate(amostras):
        if arq.exists():
            r_ = idx // 4
            c_ = idx % 4
            pv.drawImage(8 + c_ * 296, 8 + r_ * 296, QImage(str(arq)))
    pv.end()
    vitrine.save(str(caminho_saida.parent / "preview_memes_mia_zuric.png"), "PNG")


def main():
    QApplication.instance() or QApplication([])
    pets_dir = ROOT / "pets"
    pets_dir.mkdir(exist_ok=True)

    (pets_dir / "mia.json").write_text(json.dumps(MIA_JSON, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mia_dir = pets_dir / "mia"
    mia_dir.mkdir(exist_ok=True)
    (mia_dir / "recadinhos.txt").write_text(MIA_RECADINHOS, encoding="utf-8")
    (mia_dir / "recadinhos_tristes.txt").write_text(MIA_TRISTES, encoding="utf-8")
    (mia_dir / "cartazes.txt").write_text(MIA_CARTAZES, encoding="utf-8")

    sprites_dir = mia_dir / "sprites"
    sheet_ref = sprites_dir / "_sheet_ref.jpg"
    extrair_15_sprites_mia(sheet_ref, sprites_dir)
    _CACHE_SPRITES.clear()

    for emo, lista in MEMES_MIA.items():
        pasta_emo = mia_dir / "memes" / emo
        if pasta_emo.exists():
            for antigo in pasta_emo.glob("*.webp"):
                antigo.unlink()
        for nome_arq, legenda, cor, prop, chave_sp in lista:
            gerar_meme_webp(pasta_emo / f"{nome_arq}.webp", sprites_dir, legenda, cor, prop, chave_sp)

    if len(sys.argv) > 1:
        gerar_preview(Path(sys.argv[1]), sprites_dir)


if __name__ == "__main__":
    main()
