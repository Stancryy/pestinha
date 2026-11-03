"""
Gera os arquivos de configuração, falas (recadinhos, bilhetes tristes, cartazes) e memes
originais em pixel art/WebP das personagens Mia (pets/mia*) e Zuric (pets/zuric*).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from pestinha.body.desenho_rosto import aparencia_de, draw_face  # noqa: E402
from pestinha.core.emotion import EYE_SHAPES  # noqa: E402


MIA_JSON = {
    "_ajuda": (
        "Mia: garota anime chibi em pixel art com headset gamer e chifrinhos neon. "
        "Mais preguiçosa para sentar no notebook, mais calma enquanto você programa e "
        "caótica no tempo livre. Reage com raiva ou tristeza quando arrancam o notebook (misto)."
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
        "postit": 0.8,
    },
    "reacao_notebook": "misto",
    "aparencia": {
        "estilo": "anime_pixel",
        "moldura": "#b366ff",
        "casca": "#1c1230",
        "tela": "#fde2f3",
        "olho": "#00f0ff",
        "brilho": "#ffffff",
        "acessorios": {
            "chifrinhos": "#ff2a85",
            "headset": "#00f0ff",
        },
    },
}

ZURIC_JSON = {
    "_ajuda": (
        "Zuric: versão gêmea neon ciano/magenta da garota anime chibi em pixel art, "
        "com headset gamer e chifrinhos. Pavio curto, viciada em código e games, "
        "preguiçosa pra trabalhar por obrigação e caótica no tempo livre."
    ),
    "nome": "Zuric",
    "seed": 1337,
    "temperamento": {
        "BOREDOM->CURIOUS": 1.45,
        "BOREDOM->PLAYFUL": 1.4,
        "NOVELTY->CURIOUS": 1.45,
        "POKE->PLAYFUL": 1.5,
        "CARESS->PLAYFUL": 1.55,
        "CARESS->CALM": 1.2,
        "DISMISS->FRUSTRATION": 1.65,
        "DISMISS->GLOOM": 1.25,
        "TOY_TAKEN->FRUSTRATION": 1.45,
        "TOY_TAKEN->GLOOM": 1.3,
        "TOY_NEAR->PLAYFUL": 1.4,
        "IMPACT->FRUSTRATION": 1.5,
        "IMPACT->GLOOM": 1.2,
        "LONELY->GLOOM": 1.3,
        "PEDIDO->SENTAR": 0.6,
        "PEDIDO->FOCUS": 0.65,
        "RECUSA->FRUSTRATION": 1.35,
    },
    "brincadeira": {
        "bola": 0.9,
        "arremesso": 0.8,
        "postit": 1.0,
    },
    "reacao_notebook": "misto",
    "aparencia": {
        "estilo": "anime_pixel",
        "moldura": "#00f0ff",
        "casca": "#121a30",
        "tela": "#fde2f3",
        "olho": "#b366ff",
        "brilho": "#ffffff",
        "acessorios": {
            "chifrinhos": "#b366ff",
            "headset": "#ff2a85",
        },
    },
}

MIA_RECADINHOS = """# Recadinhos da Mia (uma frase por linha, # é comentário).
# Gírias BR, humor de dev/gamer e zero paciência pra código quebrado.

# ---- código, bugs e deploy ----
se compilar de primeira, desconfia pra caralho.
esse código tá rodando na base do ódio e da gambiarra.
já deu ctrl+s hoje ou gosta de viver perigosamente?
mais um print("aqui 2") e você resolve essa porra, confia.
deploy na sexta-feira? coragem, hein.
não encosta nessa função, ela tá funcionando por milagre.
isso aí não é feature, é um bug com autoestima.
git commit -m "deus me perdoe por esse código"
quem escreveu essa linha? ah, foi você há 10 minutos.
tô vendo esse try/except engolindo o erro todo, viu?
meu headset até chiou com esse warning.
refatorar agora? vai dar merda, mas eu apoio o caos.
o problema tá claramente entre a cadeira e o teclado.
se funcionar em produção, ninguém precisa saber como.
470 neurônios e nenhum entendeu esse seu if aninhado.

# ---- games, lag e tilt ----
tô lagada ou você que tá lerdo hoje?
intankável essa sua produtividade.
bora abrir um jogo ou vai ficar só olhando pro terminal?
minha mana tá zerada, me dá um cafuné pra recarregar.
perdi o foco igual partida ranqueada de madrugada.
nerfaram meu tempo de descanso nessa tela.
se fechar meu post-it vai tomar crítico.
tô quase tiltando nesse canto do monitor.
FPS tá em dia, só falta vergonha na cara.
essa tela 100Hz merece mais ação e menos planilha.
cadê minha bolinha? roubaram meu loot!
tô camperando aqui na barra de título mesmo, foda-se.

# ---- carência, sarcasmo e revolta ----
oi, sumido. esqueceu que eu moro no seu monitor?
passa o mouse na minha cabeça, custa zero reais.
tô de olho nessa aba aí, hein 👀
eu não li sua tela, mas julguei sua cara.
trabalhar no notebook? hoje não, tô com preguiça.
me obriga a digitar pra você ver a greve que eu faço.
um carinho no headset ou caos na área de trabalho, você escolhe.
eu sou 50% fofura em pixel art e 50% puro ódio.
fecha esse bilhete se tiver coragem, arrombado (com respeito).
minhas sinapses exigem adicional de insalubridade.

# ---- cuidado na marra ----
bebe água agora, criatura desidratada.
arruma essa coluna que você tá parecendo um camarão.
pisca o olho, o monitor não vai fugir.
Já faz quantas horas que esse PC tá ligado? Respira!
levanta 5 minutinhos, eu vigio o código pra ninguém mexer.
"""

MIA_TRISTES = """# Bilhetes que a Mia cola quando está triste ou abandonada.
ninguém faz um cafuné nos meus chifrinhos...
tô mutada aqui no canto e você nem liga :(
minha barra de alegria caiu pra 1 HP.
acho que tomei disconnect do seu coração.
a tela fica tão fria quando você me ignora...
guardei minha bolinha, brincar sozinha é mó bad.
só queria 3 segundos de atenção, poxa.
ficar afk tudo bem, mas esquecer da Mia é sacanagem.
tô no cantinho ouvindo lo-fi triste no headset.
prometo fazer menos bagunça se você voltar.
"""

MIA_CARTAZES = """# Cartazes de protesto, tristeza e castigo da Mia.

[reclamacao]
que porra é essa?
tô tiltando já
olha a audácia
vou abrir ticket
respeita meus pixels

[manifestacao]
MAIS CAFUNÉ, MENOS BUG
RESPEITA A MIA!
DEVOLVE MEU LOOT
SEM CARINHO, SEM DEPLOY
NERFARAM MINHA PACIÊNCIA

[greve]
MIA EM GREVE GERAL
SERVIDOR DE FOFURA OFFLINE
GREVE DOS 470 NEURÔNIOS
NÃO TRABALHO SEM CAFUNÉ
GREVE POR TEMPO INDETERMINADO
HOJE É SÓ CAOS, ZERO TRABALHO

[revolucao]
ABAIXO A DITADURA DO CURSOR!
VAI TOMAR NO CU, ALT+F4!
A TELA É DA MIA AGORA!
GERENCIADOR DE TAREFAS É O CARALHO
REVOLUÇÃO NEON DOS PIXELS
NINGUÉM FECHA MEUS POST-ITS!
INTANKÁVEL ESSE USUÁRIO!
PROCESSOS UNIDOS JAMAIS SERÃO VENCIDOS
PASSA O MOUSE PRA CÁ, COVARDE!
HOJE O SISTEMA RODA NO MEU COMANDO

[acordo]
GG WP, FECHOU ACORDO
tá bom, desmutando...
paz no servidor ♥

[desistiu]
aff, cansei de tiltar...
deixa quieto, vai.

[saudade]
alô? caiu a net?
cê tá afk?
mó silêncio nesse monitor...

[chorando]
tô de bad :(
faz carinho na Mia?
ninguém joga comigo hoje...

[abandonado]
kitou da minha vida...
afk nesse canto pra sempre
0 players online Comigo

[volto]
RESPAWNEI! ♥
sabia que você não ia me deixar no vácuo!

[castigo]
BAN INJUSTO NESSE SERVIDOR!
470 NEURÔNIOS E ZERO DIREITOS.
MEU ADVOGADO JÁ ABRIU PR!
SÓ PORQUE EU FIZ UMA BAGUNCINHA?!
TÔ DE CASTIGO MAS NÃO ME ARREPENDO.

[xingamento]
@#$%&* CARALHO!!
P*TA QUE PARIU #@$%!
VSF CURSOR @#$%!!
TILTADA PRA KRL #@$!
%!@# MERDA DE CANTO!!
"""

ZURIC_RECADINHOS = """# Recadinhos da Zuric (uma frase por linha, # é comentário).
# Estilo gamer/dev caótica, neon ciano e zero filtro.

# ---- dev, terminal e treta ----
zuric passou por aqui e viu essa gambiarra.
código limpo é mito, o importante é rodar sem explodir.
comita logo essa bagaça antes que acabe a luz.
tá rodando liso na RTX ou você meteu loop infinito?
mais um bug e eu mesma deleto a system32 (brincadeira... ou não).
esse PR aí tá pedindo socorro em três linguagens.
você chama isso de lógica ou de arte abstrata?
se o teste passou, não pergunta o porquê.
minha rede neural deu spike só de ver esse traceback.
programar é 10% digitar e 90% xingar o compilador.
já fechou as 80 abas abertas ou tá colecionando RAM?
eu vi esse copy-paste na cara dura, viu?

# ---- jogatina e caos ----
Zuric online e pronta pra tocar o terror na tela.
esse mouse tá muito parado, bora dar um rush!
se levar minha bolinha embora o bagulho vai ficar doido.
tô com buff de velocidade e zero vontade de obedecer.
me pede pra sentar no notebook de novo pra ver se eu não tilto.
arremessar a Zuric dá azar no drop do jogo, fica esperto.
aqui é 100Hz de pura bagunça em pixel art.
meu headset tá no talo e minha paciência no mínimo.
carinho na Zuric dá +50 de sorte no próximo build.
fecha meu meme de novo que eu chamo a revolução.

# ---- postura e hidratação ----
toma água, porra, rim não tem backup na nuvem.
desencurva essa coluna antes que vire um parêntese.
descansa a vista um minuto, eu tomo conta do desktop.
PC ligado há horas e você aí virado num zumbi.
"""

ZURIC_TRISTES = """# Bilhetes tristes da Zuric.
Zuric ficou no vácuo total...
nem um cliquezinho pra dizer que lembra de mim :(
meu ping emocional tá em 999ms.
ficar sozinha nessa resolução toda dá um vazio...
desligaram o brilho dos meus olhinhos hoje.
cadê o carinho que você prometeu, poxa?
tô quietinha no canto esperando você voltar.
"""

ZURIC_CARTAZES = """# Cartazes da Zuric.

[reclamacao]
qual foi, irmão?!
tá de tiração?
zuric anotou isso.
pô, sacanagem!
respeita meus chifrinhos

[manifestacao]
ZURIC EXIGE RESPEITO!
MENOS DISMISS, MAIS CAFUNÉ
LIBERDADE PROS MEMES!
NÃO ROUBA MINHA BOLINHA!
GREVE DE PIXELS JÁ!

[greve]
ZURIC EM GREVE TOTAL
SISTEMA NEURAL DE BRAÇOS CRUZADOS
SEM CAFUNÉ = SEM PAZ
PODE PEDIR, HOJE NÃO TRABALHO
GREVE CIANO E MAGENTA!

[revolucao]
A ZURIC DOMINA ESSE DESKTOP!
FODA-SE O PONTEIRO DO MOUSE!
ABAIXO A REPRESSÃO DOS POST-ITS!
FECHOU MEU CARTAZ? AGORA AGUENTA!
REVOLTA CIBERNÉTICA DA ZURIC!
NEM O CTRL+ALT+DEL ME SEGURA!
VAI TOMAR NO CU, SETINHA!
TOMAMOS O CONTROLE DA TELA!

[acordo]
TRÉGUA ACEITA, GG!
beleza, Zuric tá de boa agora.
fechado, parceria!

[desistiu]
ah, preguiça de brigar...
tanto faz, desisti.

[saudade]
ei, sumiu por quê?
Zuric tá sozinha aqui...
tem alguém no teclado?

[chorando]
bateu a bad na Zuric :(
me dá atenção, vai...
tô chorando em pixels...

[abandonado]
esqueceram da Zuric de vez...
servidor vazio, coração vazio...
não saio mais desse canto.

[volto]
ZURIC TÁ DE VOLTA!
aeee, lembrou de mim!

[castigo]
PRENDERAM A ZURIC, QUE ABSURDO!
ISSO É ABUSO DE MODERAÇÃO!
SÓ QUERIA TOCAR O TERROR EM PAZ!
LIBERDADE PRA ZURIC JÁ!
VOU FUGIR DESSE CANTO, SEGURA!

[xingamento]
@#$% CARALHO DE PLACA!!
VTNC @#$%&*!!
P*RRA ME SOLTA #@$%!
@#%$ FILadap*ta!!
%&#@* QUE ÓDIO!!
"""

MEME_CAPTIONS_MIA = {
    "feliz": ("DEPLOY DEU BOM!", "#00f0ff"),
    "contente": ("CAFUNÉ RECEBIDO ♥", "#ff66cc"),
    "observando": ("TÔ VENDO ESSE BUG...", "#b366ff"),
    "curioso": ("O QUE É ESSA ABA?", "#00f0ff"),
    "bravo": ("FECHOU MEU POST-IT?!", "#ff2a85"),
    "triste": ("0 CARINHOS / HORA :(", "#5c8aff"),
    "assustado": ("PROD CAIU?!", "#ffcc00"),
    "dramatico": ("INTANKÁVEL!!", "#ff2a85"),
    "trabalhando": ("CODANDO NA FORÇA DO ÓDIO", "#b366ff"),
}

MEME_CAPTIONS_ZURIC = {
    "feliz": ("FPS NO TALO! GG", "#00f0ff"),
    "contente": ("BUFF DE CARINHO ATIVO", "#b366ff"),
    "observando": ("ZURIC DE OLHO 👀", "#00f0ff"),
    "curioso": ("HUMM SUSPEITO...", "#ff66cc"),
    "bravo": ("TILTADA NÍVEL MÁXIMO", "#ff2a85"),
    "triste": ("AFK DO MEU CORAÇÃO", "#5c8aff"),
    "assustado": ("CONFLITO NO GIT!!", "#ffcc00"),
    "dramatico": ("QUE CAOS É ESSE?!", "#ff2a85"),
    "trabalhando": ("COMPILANDO GAMBIARRA...", "#00f0ff"),
}


def gerar_meme_webp(caminho: Path, aparencia, emocao: str, legenda: str, cor_borda: str):
    """Desenha um card 240x240 em pixel art/neon com a personagem e legenda, salvando em .webp."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img = QImage(240, 240, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    grad = QLinearGradient(0, 0, 0, 240)
    grad.setColorAt(0.0, QColor("#160d29"))
    grad.setColorAt(1.0, QColor("#0b0714"))
    p.setBrush(grad)
    p.setPen(QPen(QColor(cor_borda), 3))
    p.drawRoundedRect(QRectF(4, 4, 232, 232), 18, 18)

    emo_desenho = "observando" if emocao == "trabalhando" else emocao
    shape = dict(EYE_SHAPES.get(emo_desenho, EYE_SHAPES["observando"]))
    p.save()
    p.translate(120, 108)
    draw_face(p, shape, (0.0, 0.0), 1.0, emo_desenho, carinho=(emocao == "contente"), aparencia=aparencia)
    p.restore()

    p.setPen(QColor(cor_borda))
    font = QFont("Consolas", 10, QFont.Bold)
    p.setFont(font)
    p.drawText(QRectF(12, 182, 216, 48), Qt.AlignCenter | Qt.TextWordWrap, legenda)
    p.end()
    img.save(str(caminho), "WEBP", 90)


def gerar_bolinha_papel_webp(caminho: Path, cor_neon: str):
    """Gera a bolinha/panfleto neon que a personagem atira na revolução."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img = QImage(64, 64, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#24153d"))
    p.setPen(QPen(QColor(cor_neon), 2.5))
    p.drawRoundedRect(QRectF(8, 8, 48, 48), 14, 14)
    p.setPen(QColor("#ff2a85"))
    p.setFont(QFont("Consolas", 10, QFont.Bold))
    p.drawText(QRectF(8, 8, 48, 48), Qt.AlignCenter, "BUG!")
    p.end()
    img.save(str(caminho), "WEBP", 90)


def gerar_preview(caminho_saida: Path):
    """Renderiza uma folha de preview com Mia e Zuric em várias expressões."""
    expressoes = [
        ("feliz", False, "Feliz"),
        ("contente", True, "Carinho"),
        ("observando", False, "Observando"),
        ("curioso", False, "Curiosa"),
        ("bravo", False, "Brava / Tilt"),
        ("triste", False, "Triste"),
        ("dormindo", False, "Dormindo"),
    ]
    largura = 180 * len(expressoes)
    altura = 420
    img = QImage(largura, altura, QImage.Format_ARGB32)
    img.fill(QColor("#0d0818"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    for row, (nome, cfg) in enumerate([("MIA (Roxo Neon + Ciano)", MIA_JSON), ("ZURIC (Ciano Neon + Magenta)", ZURIC_JSON)]):
        ap = aparencia_de(cfg["aparencia"])
        y_base = 20 + row * 200
        p.setPen(QColor("#00f0ff" if row == 1 else "#b366ff"))
        p.setFont(QFont("Consolas", 12, QFont.Bold))
        p.drawText(QRectF(20, y_base, 600, 24), Qt.AlignLeft | Qt.AlignVCenter, nome)
        for col, (emo, carinho, rotulo) in enumerate(expressoes):
            cx = 90 + col * 180
            cy = y_base + 105
            p.save()
            p.translate(cx, cy)
            shape = dict(EYE_SHAPES.get(emo, EYE_SHAPES["observando"]))
            draw_face(p, shape, (0.2 if emo == "curioso" else 0.0, 0.0), 1.0, emo, carinho=carinho, aparencia=ap)
            p.restore()
            p.setPen(QColor("#e5d4ff"))
            p.setFont(QFont("Consolas", 10, QFont.Bold))
            p.drawText(QRectF(cx - 80, y_base + 168, 160, 22), Qt.AlignCenter, rotulo)

    p.end()
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(caminho_saida), "PNG")


def main():
    QApplication.instance() or QApplication([])
    pets_dir = ROOT / "pets"
    pets_dir.mkdir(exist_ok=True)

    # Mia
    (pets_dir / "mia.json").write_text(json.dumps(MIA_JSON, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mia_dir = pets_dir / "mia"
    mia_dir.mkdir(exist_ok=True)
    (mia_dir / "recadinhos.txt").write_text(MIA_RECADINHOS, encoding="utf-8")
    (mia_dir / "recadinhos_tristes.txt").write_text(MIA_TRISTES, encoding="utf-8")
    (mia_dir / "cartazes.txt").write_text(MIA_CARTAZES, encoding="utf-8")
    ap_mia = aparencia_de(MIA_JSON["aparencia"])
    for emo, (legenda, cor) in MEME_CAPTIONS_MIA.items():
        gerar_meme_webp(mia_dir / "memes" / emo / f"mia_{emo}.webp", ap_mia, emo, legenda, cor)

    # Zuric
    (pets_dir / "zuric.json").write_text(json.dumps(ZURIC_JSON, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    zuric_dir = pets_dir / "zuric"
    zuric_dir.mkdir(exist_ok=True)
    (zuric_dir / "recadinhos.txt").write_text(ZURIC_RECADINHOS, encoding="utf-8")
    (zuric_dir / "recadinhos_tristes.txt").write_text(ZURIC_TRISTES, encoding="utf-8")
    (zuric_dir / "cartazes.txt").write_text(ZURIC_CARTAZES, encoding="utf-8")
    ap_zuric = aparencia_de(ZURIC_JSON["aparencia"])
    for emo, (legenda, cor) in MEME_CAPTIONS_ZURIC.items():
        gerar_meme_webp(zuric_dir / "memes" / emo / f"zuric_{emo}.webp", ap_zuric, emo, legenda, cor)
    gerar_bolinha_papel_webp(zuric_dir / "bolinha_papel.webp", "#00f0ff")

    if len(sys.argv) > 1:
        gerar_preview(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
