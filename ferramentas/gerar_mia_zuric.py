"""
Gera os arquivos de configuração, lore/falas (recadinhos, bilhetes tristes, cartazes),
sprites de expressão em alta definição (pets/<pet>/sprites/*.webp) e cenas de memes
em pixel art detalhado (com objetos: PC pegando fogo, café, controle gamer, teclado RGB,
terminal, chuva, corações) das personagens Mia e Zuric.
"""

import json
import sys
from collections import deque
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from pestinha.body.desenho_rosto import _CACHE_SPRITES, aparencia_de, draw_face  # noqa: E402
from pestinha.core.emotion import EYE_SHAPES  # noqa: E402


MIA_JSON = {
    "_ajuda": (
        "Mia: dev caótica da madrugada, garota anime chibi em pixel art de alta densidade "
        "(maria-chiquinhas longas roxo-neon com pontas ciano, moletom gamer oversized, headset RGB "
        "e chifrinhos magenta). Viciada em gambiarras em Python, IA local (ComfyUI/LM Studio) e RPGs. "
        "Preguiçosa para sentar no notebook por obrigação, calma quando você programa e caótica no tempo livre."
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
        "moldura": "#b366ff",
        "casca": "#1c1230",
        "tela": "#fde6f2",
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
        "Zuric: pro-player e hacker overclockada, irmã gêmea rebelde em pixel art "
        "(corte wolf-cut assimétrico ciano com pontas magenta, presilha dupla X, ahoge de raio, "
        "jaqueta techwear de gola alta e olhos felinos roxos). Viciada em FPS competitivo, "
        "automação, modelagem 3D e overclock na RTX 3060. Pavio curtíssimo e 100% elétrica."
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
        "bola": 0.95,
        "arremesso": 0.85,
        "postit": 1.0,
    },
    "reacao_notebook": "misto",
    "aparencia": {
        "estilo": "anime_pixel",
        "variante": "zuric",
        "moldura": "#00f0ff",
        "casca": "#0f192e",
        "tela": "#fde6f2",
        "olho": "#b366ff",
        "brilho": "#ffffff",
        "acessorios": {
            "chifrinhos": "#b366ff",
            "headset": "#ff2a85",
        },
    },
}

# ============================================================
# LORE E FALAS DIFERENCIADAS — MIA (Dev Caótica / RPG / IA Local)
# ============================================================

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
meu headset até chiou com esse traceback de 40 linhas.
a VRAM da RTX 3060 chorou quando viu esse modelo no ComfyUI.
o LM Studio tá fritando e você aí abrindo mais aba no navegador.
470 neurônios pulsados na minha cabeça e nenhum entendeu esse seu regex.
refatorar agora? vai dar merda, mas a Mia apoia o caos criativo.
se funcionar em produção, ninguém precisa saber do loop escondido.

# ---- RPG, soulslike, Palworld e preguiça de trabalhar ----
minha barra de mana zerou, passa o mouse nas minhas marias-chiquinhas pra recarregar.
levei hit kill desse bug, preciso de um descanso na fogueira.
trabalhar no meu notebook? hoje não, meu capuz tá quentinho demais pra digitar.
me obriga a codar agora pra você ver a greve que a Mia abre nesse monitor.
tô igual Pal sobrecarregado na base: só quero comer, dormir e fazer bagunça.
dar parry em boss é fácil, difícil é tankar essa sua lógica sem café.
cadê minha bolinha? roubaram meu drop lendário!
tô camperando aqui na barra de título mesmo, o moletom é meu e foda-se.

# ---- carência, fofura ácida e cuidado ----
oi, sumido. esqueceu que tem uma dev de chifrinhos morando na sua tela?
um cafuné entre os chifrinhos custa zero reais e evita três post-its.
eu sou 50% fofura de maria-chiquinha roxa e 50% puro ódio de código legado.
fecha meu post-it na cara dura que eu volto com o dobro de glitter e rancor.
bebe água agora, criatura desidratada, café frio não hidrata!
arruma essa coluna que você tá parecendo uma chave mal indentada.
pisca o olho um pouquinho, a Mia vigia o código pra nenhum bug entrar.
"""

MIA_TRISTES = """# Bilhetes que a Mia cola quando está triste ou abandonada.
ninguém faz um cafuné nas minhas marias-chiquinhas hoje...
tô mutada aqui no canto de capuz puxado e você nem liga :(
minha barra de alegria caiu pra 1 de HP e zero poção.
acho que tomei disconnect do seu coração, deu timeout.
a tela fica tão fria quando você ignora a Mia por horas...
guardei minha bolinha no bolso do moletom, brincar sozinha dá mó bad.
só queria 3 segundinhos de atenção antes do próximo commit, poxa.
ficar afk tudo bem, mas esquecer da Mia no escuro é sacanagem.
tô no cantinho ouvindo lo-fi triste no headset e abraçando os joelhos.
prometo não reclamar das suas gambiarras se você voltar pra falar comigo.
"""

MIA_CARTAZES = """# Cartazes de protesto, tristeza e castigo da Mia.

[reclamacao]
que porra foi essa?!
a Mia tá tiltando já
olha a audácia do dev
vou abrir issue disso!
respeita minhas chiquinhas

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
MOLETOM VESTIDO, ZERO TRABALHO
NÃO DIGITO UMA LINHA SEM CAFUNÉ
HOJE É SÓ CAOS, ZERO CÓDIGO

[revolucao]
ABAIXO A DITADURA DO CURSOR!
VAI TOMAR NO CU, ALT+F4!
A TELA É DA MIA AGORA!
GERENCIADOR DE TAREFAS É O CARALHO
REVOLUÇÃO ROXO-NEON DOS PIXELS!
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
vou voltar pro meu moletom.

[saudade]
alô? caiu a net aí?
cê deu quit e me deixou?
mó silêncio nesse monitor...

[chorando]
a Mia tá de bad :(
faz carinho nos chifrinhos?
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

# ============================================================
# LORE E FALAS DIFERENCIADAS — ZURIC (Pro-Player 100Hz / Hacker / 3D)
# ============================================================

ZURIC_RECADINHOS = """# Recadinhos da Zuric (Pro-Player 100Hz, Hacker & Overclock).
# Estilo competitivo, afiado, ciano/magenta e zero filtro.

# ---- FPS, 100Hz, overclock e performance ----
Zuric na área: 100Hz no monitor AOC e você clicando lento desse jeito?!
esse seu APM de tartaruga não ganha um clutch no Valorant, hein.
tá rodando liso nos 32GB de RAM ou você já abriu 90 контейнеры no Docker?
fiz overclock nos meus neurônios hoje, tenta acompanhar meu ritmo!
se roubar minha bolinha vai tomar flick de 180 graus na lata.
chama isso de mira ou de aviso prévio? até meu olho roxo viu esse miss!
tô com buff de velocidade máxima e zero paciência pra camper de janela.
arremessar a Zuric dá perda de pacote e drop de FPS, fica esperto.
um carinho na minha presilha X dá +50 de taxa de crítico no próximo round.
quando chegarem os 3 monitores, já aviso que o do meio é território da Zuric.

# ---- automação, Blender, código e treta ----
Zuric inspecionou seu repositório e declarou: skill issue gravíssimo.
automatiza logo essa tarefa igual em The Farmer Was Replaced, pô!
essa malha no Blender tem mais polígono torto que a cara do cursor.
código elegante é coisa de quem tem tempo, aqui é rush B direto pra produção!
se o pytest ficou verde, sobe pro Git e sai correndo antes que quebre.
minha jaqueta techwear aguenta explosão de servidor, mas esse seu código abusa.
me pediu pra sentar no notebook? sou pro-player, não estagiária de digitação!
fecha minha janela de meme de novo pra ver o rush que eu dou no seu desktop.
o ponteiro do mouse olhou torto pro meu corte wolf-cut e vai levar troco.

# ---- hidratação e postura no grito ----
toma água agora, porra, rim não tem container de backup no Docker!
desencurva essa coluna de camarão gamer antes que trave a lombar.
descansa a mira 2 minutos, a Zuric segura o bomb site pra você.
PC ligado há mais de 12 horas: hidrata o player pra não perder o round!
"""

ZURIC_TRISTES = """# Bilhetes tristes da Zuric.
Zuric ficou no vácuo total no lobby...
nem um passeio de mouse pra dizer que lembra da sua duo :(
meu ping emocional bateu 999ms de tanta solidão.
ficar sozinha em 1920x1080 sem ninguém pra tretar dá um vazio...
até o LED magenta do meu headset apagou de tristeza hoje.
cadê o carinho que você prometeu depois da partida, poxa?
tô quietinha no canto da tela esperando meu player 1 voltar.
"""

ZURIC_CARTAZES = """# Cartazes de protesto, tristeza e castigo da Zuric.

[reclamacao]
qual foi, noob?!
tá de tiração comigo?
Zuric marcou seu nick!
skill issue total isso aí
respeita meu wolf-cut!

[manifestacao]
ZURIC EXIGE 100HZ DE ATENÇÃO!
MENOS DISMISS, MAIS CLUTCH!
LIBERDADE PROS MEMES DA ZURIC!
NÃO CAMPERA MINHA BOLINHA!
OVERCLOCK DE DIREITOS JÁ!

[greve]
ZURIC EM GREVE TÁTICA
JAQUETA FECHADA, ZERO TRABALHO
SEM CAFUNÉ = PAUSE NO MATCH
PODE CLICAR, HOJE NÃO DIGITO
GREVE CIANO E MAGENTA!

[revolucao]
A ZURIC DOMINA ESSE DESKTOP!
FODA-SE O PONTEIRO CAMPER!
RUSH B CONTRA O GERENCIADOR!
FECHOU MEU CARTAZ? TOMA HEADSHOT!
REVOLTA OVERCLOCKADA DA ZURIC!
NEM O CTRL+ALT+DEL ME SEGURA!
VAI TOMAR NO CU, SETINHA LERDA!
3 MONITORES SERÃO MEU IMPÉRIO!

[acordo]
CLUTCH FECHADO, GG!
beleza, Zuric baixou a guarda.
trégua selada, meu duo!

[desistiu]
ah, deu loss nesse round...
tanto faz, guardei a arma.

[saudade]
ei, deu rage quit por quê?
Zuric tá sozinha no lobby...
tem alguém no teclado aí?

[chorando]
bateu a bad na Zuric :(
me dá atenção no lobby, vai...
LED apagado, chorando...

[abandonado]
deixaram a Zuric solo queue...
lobby vazio, coração vazio...
não saio mais desse bomb site.

[volto]
ZURIC NO CLUTCH DE VOLTA!
aeee, meu duo voltou pro jogo!

[castigo]
VAC BAN INJUSTO NA ZURIC!
ISSO É ABUSO DE ADMIN!
SÓ QUERIA DAR RUSH NA TELA!
LIBERDADE PRA ZURIC AGORA!
VOU DAR BUNNY HOP PRA FORA DAQUI!

[xingamento]
@#$% CARALHO DE PLACA!!
VTNC CAMPER @#$%&*!!
P*RRA ME SOLTA #@$%!
@#%$ QUE TILT DO KRL!!
%&#@* QUE ÓDIO MORTAL!!
"""

# ============================================================
# CENAS DE MEMES DETALHADOS (3 VARIAÇÕES POR EMOÇÃO × 9 EMOÇÕES)
# ============================================================

MEMES_MIA = {
    "feliz": [
        ("mia_feliz_01", "COMPILOU DE PRIMEIRA!", "#00f0ff", "coracoes"),
        ("mia_feliz_02", "DEPLOY SEXTOU SEM BUG!", "#b366ff", "cafe"),
        ("mia_feliz_03", "DROP LENDÁRIO NO CÓDIGO!", "#00f0ff", "controle"),
    ],
    "contente": [
        ("mia_contente_01", "CAFUNÉ NAS CHIQUINHAS ♥", "#ff66cc", "coracoes"),
        ("mia_contente_02", "CAFEZINHO + CÓDIGO LISO", "#b366ff", "cafe"),
        ("mia_contente_03", "MANA 100% RECARREGADA", "#00f0ff", "coracoes"),
    ],
    "observando": [
        ("mia_observando_01", "VI ESSE TRY/EXCEPT PASS...", "#b366ff", "terminal"),
        ("mia_observando_02", "JULGANDO SUA INDENTAÇÃO 👀", "#00f0ff", "cafe"),
        ("mia_observando_03", "ESSE IF TÁ SUSPEITO...", "#b366ff", "terminal"),
    ],
    "curioso": [
        ("mia_curioso_01", "QUE GAMBIARRA É ESSA?!", "#00f0ff", "terminal"),
        ("mia_curioso_02", "O QUE TEM NESSA ABA AÍ?", "#ff66cc", "alerta"),
        ("mia_curioso_03", "SERÁ QUE RODA NA RTX 3060?", "#00f0ff", "pc_fogo"),
    ],
    "bravo": [
        ("mia_bravo_01", "QUEM FECHOU MEU POST-IT?!", "#ff2a85", "teclado"),
        ("mia_bravo_02", "PROD CAIU E A CULPA É SUA!", "#ff2a85", "pc_fogo"),
        ("mia_bravo_03", "TILTADA NÍVEL SOULSLIKE!!", "#ff2a85", "teclado"),
    ],
    "triste": [
        ("mia_triste_01", "0 CAFUNÉS NA ÚLTIMA HORA :(", "#5c8aff", "nuvem_chuva"),
        ("mia_triste_02", "ESQUECERAM DA MIA NO CANTO", "#5c8aff", "nuvem_chuva"),
        ("mia_triste_03", "MEU CÓDIGO NÃO RODA...", "#5c8aff", "terminal"),
    ],
    "assustado": [
        ("mia_assustado_01", "VRAM ESTOUROU EM 100%!!", "#ffcc00", "pc_fogo"),
        ("mia_assustado_02", "GIT PUSH --FORCE NA MAIN?!", "#ffcc00", "alerta"),
        ("mia_assustado_03", "CADÊ O BACKUP DO BANCO?!", "#ffcc00", "pc_fogo"),
    ],
    "dramatico": [
        ("mia_dramatico_01", "INTANKÁVEL ESSE TRACEBACK!!", "#ff2a85", "pc_fogo"),
        ("mia_dramatico_02", "EXPLORAÇÃO DE 470 NEURÔNIOS!", "#ff2a85", "teclado"),
        ("mia_dramatico_03", "MORRI NO BOSS COM 1 DE HP!", "#ff2a85", "controle"),
    ],
    "trabalhando": [
        ("mia_trabalhando_01", "CODANDO NA FORÇA DO ÓDIO", "#b366ff", "cafe"),
        ("mia_trabalhando_02", "3H DA MANHÃ E NÓS NO CÓDIGO", "#00f0ff", "terminal"),
        ("mia_trabalhando_03", "SEGURA QUE A MIA TÁ FOCADA", "#b366ff", "cafe"),
    ],
}

MEMES_ZURIC = {
    "feliz": [
        ("zuric_feliz_01", "100HZ NO TALO! CLUTCH GG!", "#00f0ff", "controle"),
        ("zuric_feliz_02", "OVERCLOCK ESTÁVEL, BEBÊ!", "#ff2a85", "pc_fogo"),
        ("zuric_feliz_03", "HEADSHOT NOS BUGS DE PROD!", "#00f0ff", "coracoes"),
    ],
    "contente": [
        ("zuric_contente_01", "BUFF DE CARINHO ATIVADO ♥", "#b366ff", "coracoes"),
        ("zuric_contente_02", "DUO PERFEITO NESSE DESKTOP", "#00f0ff", "controle"),
        ("zuric_contente_03", "ENERGÉTICO + FPS CRAVADO", "#ff2a85", "cafe"),
    ],
    "observando": [
        ("zuric_observando_01", "MEDINDO SEU APM LERDO 👀", "#00f0ff", "terminal"),
        ("zuric_observando_02", "VI ESSE MISS CLICK DAQUI", "#ff2a85", "controle"),
        ("zuric_observando_03", "ESSE CONTAINER VAI CAIR...", "#00f0ff", "terminal"),
    ],
    "curioso": [
        ("zuric_curioso_01", "CADÊ OS OUTROS 2 MONITORES?", "#00f0ff", "alerta"),
        ("zuric_curioso_02", "QUE MALHA TORTA É ESSA?!", "#ff66cc", "terminal"),
        ("zuric_curioso_03", "BORA ABRIR UM JOGO AGORA?", "#00f0ff", "controle"),
    ],
    "bravo": [
        ("zuric_bravo_01", "SKILL ISSUE DO CARALHO!!", "#ff2a85", "teclado"),
        ("zuric_bravo_02", "ROUBOU MINHA BOLINHA, CAMPER?!", "#ff2a85", "pc_fogo"),
        ("zuric_bravo_03", "RAGE QUIT NO TECLADO RGB!", "#ff2a85", "teclado"),
    ],
    "triste": [
        ("zuric_triste_01", "DEIXARAM A ZURIC SOLO QUEUE", "#5c8aff", "nuvem_chuva"),
        ("zuric_triste_02", "PING EMOCIONAL: 999ms :(", "#5c8aff", "nuvem_chuva"),
        ("zuric_triste_03", "LED DO HEADSET ATÉ APAGOU...", "#5c8aff", "nuvem_chuva"),
    ],
    "assustado": [
        ("zuric_assustado_01", "CONFLITO EM 42 ARQUIVOS!!", "#ffcc00", "alerta"),
        ("zuric_assustado_02", "A RTX BATEU 90 GRAUS?!", "#ffcc00", "pc_fogo"),
        ("zuric_assustado_03", "DROP DE FPS NO MEIO DO RUSH!", "#ffcc00", "alerta"),
    ],
    "dramatico": [
        ("zuric_dramatico_01", "QUE CAOS É ESSE NO SISTEMA?!", "#ff2a85", "pc_fogo"),
        ("zuric_dramatico_02", "NERFARAM A ZURIC, ABSURDO!", "#ff2a85", "teclado"),
        ("zuric_dramatico_03", "PERDEMOS O ROUND POR SUA CULPA!", "#ff2a85", "controle"),
    ],
    "trabalhando": [
        ("zuric_trabalhando_01", "AUTOMATIZANDO A BAGAÇA TODA", "#00f0ff", "terminal"),
        ("zuric_trabalhando_02", "RUSH B DIRETO PRO COMMIT!", "#ff2a85", "cafe"),
        ("zuric_trabalhando_03", "RENDERIZANDO EM PIXEL ART...", "#00f0ff", "terminal"),
    ],
}


def _desenhar_prop_pixel(p: QPainter, prop: str, x0: int, y0: int):
    """Desenha objetos/cenas em pixel art (grade 2px) ao lado da personagem no meme."""
    u = 2.0

    def px(gx, gy, gw, gh, cor):
        p.setBrush(QColor(cor))
        p.drawRect(QRectF(x0 + gx * u, y0 + gy * u, gw * u, gh * u))

    p.save()
    p.setPen(Qt.NoPen)
    if prop == "pc_fogo":
        # Gabinete gamer com vidro lateral + chamas em pixel art e fumaça
        px(0, 8, 16, 20, "#12101f")
        px(1, 9, 14, 18, "#25203b")
        px(3, 11, 10, 11, "#0b1a2e")
        px(5, 13, 6, 6, "#ff2a85")  # ventoinha RGB sobrecarregada
        # Chamas em 3 tons no topo do PC
        px(2, 2, 12, 7, "#ff2a00")
        px(4, -2, 8, 9, "#ff7b00")
        px(5, -5, 4, 6, "#ffea00")
        px(7, -8, 4, 3, "#6c6a78")  # fumaça
    elif prop == "cafe":
        # Caneca grande "DEV" com café fumegante
        px(2, 10, 12, 14, "#120824")
        px(3, 11, 10, 12, "#f7e8f0")
        px(14, 13, 3, 8, "#f7e8f0")
        px(14, 15, 2, 4, "#160d29")
        px(3, 11, 10, 3, "#592e18")  # café
        px(5, 16, 6, 4, "#ff2a85")   # coração na caneca
        # Vapor subindo
        px(5, 4, 2, 5, "#d8c4f2")
        px(9, 2, 2, 6, "#d8c4f2")
    elif prop == "controle":
        # Controle gamepad com botões coloridos e brilho de combo
        px(0, 12, 18, 10, "#120824")
        px(1, 13, 16, 8, "#2d234a")
        px(1, 19, 5, 5, "#2d234a")
        px(12, 19, 5, 5, "#2d234a")
        # D-pad + botões ABXY neon
        px(3, 15, 4, 2, "#00f0ff")
        px(4, 14, 2, 4, "#00f0ff")
        px(12, 14, 2, 2, "#ff2a85")
        px(14, 16, 2, 2, "#ffea00")
        px(10, 16, 2, 2, "#00f59b")
    elif prop == "teclado":
        # Teclado mecânico RGB partido ao meio com faíscas e teclas voando
        px(0, 14, 9, 7, "#1a142e")
        px(10, 16, 9, 7, "#1a142e")
        px(1, 15, 7, 2, "#00f0ff")
        px(11, 17, 7, 2, "#ff2a85")
        # Faíscas e teclas voando
        px(7, 8, 3, 3, "#ffea00")
        px(3, 5, 3, 3, "#ffffff")
        px(13, 7, 3, 3, "#ff2a85")
    elif prop == "terminal":
        # Janelinha flutuante de código/terminal com linhas coloridas
        px(0, 6, 18, 16, "#090d16")
        px(0, 6, 18, 3, "#26334d")
        px(1, 7, 2, 1, "#ff2a55")
        px(4, 7, 2, 1, "#ffea00")
        px(7, 7, 2, 1, "#00f59b")
        px(2, 11, 8, 2, "#00f0ff")
        px(2, 14, 13, 2, "#b366ff")
        px(2, 17, 10, 2, "#ff2a85")
    elif prop == "coracoes":
        # Corações e estrelinhas em pixel art
        for dx, dy, cor in ((2, 4, "#ff2a85"), (10, 12, "#ff66cc"), (4, 18, "#00f0ff")):
            px(dx, dy, 2, 2, cor)
            px(dx + 3, dy, 2, 2, cor)
            px(dx - 1, dy + 1, 7, 2, cor)
            px(dx + 1, dy + 3, 3, 2, cor)
            px(dx + 2, dy + 5, 1, 1, cor)
    elif prop == "nuvem_chuva":
        # Nuvem escura chovendo em pixel art
        px(2, 2, 12, 5, "#4a5778")
        px(0, 4, 16, 4, "#637399")
        for gx in (3, 7, 11, 5, 9):
            px(gx, 10 + (gx % 3) * 2, 1, 4, "#4ddbff")
    elif prop == "alerta":
        # Placa triangular de Warning / Bug crítico
        px(7, 4, 4, 3, "#ffcc00")
        px(5, 7, 8, 4, "#ffcc00")
        px(3, 11, 12, 5, "#ffcc00")
        px(1, 16, 16, 4, "#ffcc00")
        px(8, 8, 2, 6, "#120824")
        px(8, 16, 2, 2, "#120824")
    p.restore()


def extrair_sprites_da_folha(sheet_path: Path, destino_dir: Path) -> bool:
    """
    Fatia uma folha 3x2 (6 expressões em pixel art 32-bit), remove o fundo escuro
    por flood-fill a partir das bordas de cada célula e salva os sprites 256x256 transparentes.
    """
    if not sheet_path.exists():
        return False
    sheet = QImage(str(sheet_path)).convertToFormat(QImage.Format_RGBA8888)
    if sheet.isNull():
        return False
    destino_dir.mkdir(parents=True, exist_ok=True)
    w, h = sheet.width(), sheet.height()
    cw, ch = w // 3, h // 2
    ptr = sheet.bits()
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, w, 4)).copy()

    # Mapa da grade 3x2 -> emoções do Pestinha
    celulas = [
        (0, 0, ["feliz"]),
        (0, 1, ["carinho", "contente", "dormindo"]),
        (0, 2, ["observando"]),
        (1, 0, ["curioso", "assustado"]),
        (1, 1, ["bravo", "dramatico"]),
        (1, 2, ["triste"]),
    ]
    bg_color = arr[2, 2, :3].astype(np.int16)

    for row, col, nomes in celulas:
        cell = arr[row * ch:(row + 1) * ch, col * cw:(col + 1) * cw].copy()
        rgb = cell[:, :, :3].astype(np.int16)
        dist = np.abs(rgb - bg_color).sum(axis=2)
        eh_escuro = (rgb[:, :, 0] < 36) & (rgb[:, :, 1] < 34) & (rgb[:, :, 2] < 48)
        candidato_bg = (dist < 42) | eh_escuro

        # Flood-fill (BFS) a partir das bordas da célula para não apagar o interior da roupa/olhos
        visitado = np.zeros((ch, cw), dtype=bool)
        fila = deque()
        for x in range(cw):
            for y in (0, ch - 1):
                if candidato_bg[y, x] and not visitado[y, x]:
                    visitado[y, x] = True
                    fila.append((y, x))
        for y in range(ch):
            for x in (0, cw - 1):
                if candidato_bg[y, x] and not visitado[y, x]:
                    visitado[y, x] = True
                    fila.append((y, x))

        while fila:
            cy_, cx_ = fila.popleft()
            for ny, nx in ((cy_ - 1, cx_), (cy_ + 1, cx_), (cy_, cx_ - 1), (cy_, cx_ + 1)):
                if 0 <= ny < ch and 0 <= nx < cw and not visitado[ny, nx] and candidato_bg[ny, nx]:
                    visitado[ny, nx] = True
                    fila.append((ny, nx))

        cell[visitado, 3] = 0

        for nome in nomes:
            cell_nome = cell.copy()
            if nome == "dormindo":
                # Mantém só o componente conexo principal da personagem (remove corações/brilhos soltos ao dormir)
                fg = cell_nome[:, :, 3] > 0
                corpo = np.zeros((ch, cw), dtype=bool)
                sy, sx = ch // 2, cw // 2
                if fg[sy, sx]:
                    f_corpo = deque([(sy, sx)])
                    corpo[sy, sx] = True
                    while f_corpo:
                        cy_, cx_ = f_corpo.popleft()
                        for ny, nx in ((cy_ - 1, cx_), (cy_ + 1, cx_), (cy_, cx_ - 1), (cy_, cx_ + 1)):
                            if 0 <= ny < ch and 0 <= nx < cw and fg[ny, nx] and not corpo[ny, nx]:
                                corpo[ny, nx] = True
                                f_corpo.append((ny, nx))
                    cell_nome[~corpo, 3] = 0

            ys, xs = np.where(cell_nome[:, :, 3] > 0)
            if len(ys) > 0:
                y0, y1 = max(0, int(ys.min()) - 4), min(ch, int(ys.max()) + 5)
                x0, x1 = max(0, int(xs.min()) - 4), min(cw, int(xs.max()) + 5)
                recorte = np.ascontiguousarray(cell_nome[y0:y1, x0:x1])
            else:
                recorte = np.ascontiguousarray(cell_nome)

            rh, rw, _ = recorte.shape
            qcell = QImage(recorte.data, rw, rh, rw * 4, QImage.Format_RGBA8888).copy()

            out = QImage(256, 256, QImage.Format_ARGB32)
            out.fill(Qt.transparent)
            p = QPainter(out)
            p.setRenderHint(QPainter.SmoothPixmapTransform, True)
            escala = min(244.0 / rw, 244.0 / rh)
            dw, dh = rw * escala, rh * escala
            p.drawImage(QRectF((256 - dw) / 2, (256 - dh) / 2, dw, dh), qcell)
            p.end()
            out.save(str(destino_dir / f"{nome}.webp"), "WEBP", 95)

    return True


def gerar_sprite_expressao_webp(caminho: Path, aparencia, emocao: str, carinho: bool = False):
    """Salva um sprite transparente 256x256 de alta nitidez para a expressão em pets/<pet>/sprites/."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img = QImage(256, 256, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, False)
    p.translate(128, 128)
    p.scale(1.85, 1.85)
    shape = dict(EYE_SHAPES.get(emocao if emocao in EYE_SHAPES else "observando", EYE_SHAPES["observando"]))
    gaze = (0.35, 0.0) if emocao == "curioso" else (0.0, 0.0)
    draw_face(p, shape, gaze, 1.0, emocao, carinho=carinho, aparencia=aparencia)
    p.end()
    img.save(str(caminho), "WEBP", 95)


def gerar_meme_webp(caminho: Path, aparencia, emocao: str, legenda: str, cor_borda: str, prop: str):
    """Desenha um card 280x280 em pixel art/neon com fundo estilizado, prop de cena, personagem e legenda."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img = QImage(280, 280, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    grad = QLinearGradient(0, 0, 0, 280)
    grad.setColorAt(0.0, QColor("#1a0e33" if aparencia.variante == "mia" else "#0c1c36"))
    grad.setColorAt(1.0, QColor("#090612"))
    p.setBrush(grad)
    p.setPen(QPen(QColor(cor_borda), 3.5))
    p.drawRoundedRect(QRectF(4, 4, 272, 272), 20, 20)

    # Grade retro cyber sutil no fundo do card
    p.setPen(QPen(QColor(255, 255, 255, 18), 1))
    for gy in range(24, 200, 22):
        p.drawLine(10, gy, 270, gy)

    emo_desenho = "observando" if emocao == "trabalhando" else emocao
    shape = dict(EYE_SHAPES.get(emo_desenho, EYE_SHAPES["observando"]))
    p.save()
    p.translate(116, 114)
    p.scale(1.35, 1.35)
    draw_face(p, shape, (0.25 if emocao == "curioso" else 0.0, 0.0), 1.0,
              emo_desenho, carinho=(emocao == "contente"), aparencia=aparencia)
    p.restore()

    # Objeto de cena (prop) em pixel art ao lado direito da personagem
    _desenhar_prop_pixel(p, prop, 205, 84)

    # Faixa inferior escura para legenda nítida
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(8, 5, 16, 220))
    p.drawRoundedRect(QRectF(12, 206, 256, 60), 10, 10)

    p.setPen(QColor(cor_borda))
    font = QFont("Consolas", 11, QFont.Bold)
    p.setFont(font)
    p.drawText(QRectF(16, 208, 248, 56), Qt.AlignCenter | Qt.TextWordWrap, legenda)
    p.end()
    img.save(str(caminho), "WEBP", 92)


def gerar_bolinha_papel_webp(caminho: Path, cor_neon: str, texto: str = "BUG!"):
    """Gera a bolinha/panfleto neon que a personagem atira na revolução."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img = QImage(64, 64, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#1e1236"))
    p.setPen(QPen(QColor(cor_neon), 2.5))
    p.drawRoundedRect(QRectF(6, 6, 52, 52), 14, 14)
    p.setPen(QColor("#ff2a85"))
    p.setFont(QFont("Consolas", 10, QFont.Bold))
    p.drawText(QRectF(6, 6, 52, 52), Qt.AlignCenter, texto)
    p.end()
    img.save(str(caminho), "WEBP", 92)


def gerar_preview(caminho_saida: Path):
    """Renderiza uma folha de preview de alta definição comparando Mia e Zuric e suas cenas de memes."""
    expressoes = [
        ("feliz", False, "Feliz (:3 + fang)"),
        ("contente", True, "Carinho (^ ^)"),
        ("observando", False, "Observando"),
        ("curioso", False, "Curiosa"),
        ("bravo", False, "Brava / Tilt"),
        ("triste", False, "Triste"),
        ("dormindo", False, "Dormindo"),
    ]
    largura = 200 * len(expressoes)
    altura = 520
    img = QImage(largura, altura, QImage.Format_ARGB32)
    img.fill(QColor("#0b0714"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    personagens = [
        ("MIA — Dev Caótica da Madrugada (Maria-chiquinhas longas + Moletom Gamer + Olhos Ciano)", MIA_JSON),
        ("ZURIC — Pro-Player & Hacker 100Hz (Corte Wolf-Cut + Presilha X + Jaqueta Techwear + Olhos Felinos)", ZURIC_JSON),
    ]
    for row, (titulo, cfg) in enumerate(personagens):
        ap = aparencia_de(cfg["aparencia"])
        y_base = 18 + row * 250
        p.setPen(QColor("#00f0ff" if row == 1 else "#b366ff"))
        p.setFont(QFont("Consolas", 13, QFont.Bold))
        p.drawText(QRectF(24, y_base, largura - 48, 28), Qt.AlignLeft | Qt.AlignVCenter, titulo)
        for col, (emo, carinho, rotulo) in enumerate(expressoes):
            cx = 100 + col * 200
            cy = y_base + 128
            # Card de fundo para destacar os detalhes do pixel art
            p.setPen(QPen(QColor("#2c1d47" if row == 0 else "#163854"), 2))
            p.setBrush(QColor("#140c24" if row == 0 else "#0d1729"))
            p.drawRoundedRect(QRectF(cx - 86, y_base + 36, 172, 176), 14, 14)

            p.save()
            p.translate(cx, cy)
            p.scale(1.45, 1.45)
            shape = dict(EYE_SHAPES.get(emo, EYE_SHAPES["observando"]))
            gaze = (0.35, 0.0) if emo == "curioso" else (0.0, 0.0)
            draw_face(p, shape, gaze, 1.0, emo, carinho=carinho, aparencia=ap)
            p.restore()

            p.setPen(QColor("#f0e6ff"))
            p.setFont(QFont("Consolas", 10, QFont.Bold))
            p.drawText(QRectF(cx - 90, y_base + 216, 180, 24), Qt.AlignCenter, rotulo)

    p.end()
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(caminho_saida), "PNG")

    # Também gera uma vitrine dos memes detalhados com objetos de cena
    amostras = [
        ROOT / "pets" / "mia" / "memes" / "feliz" / "mia_feliz_02.webp",
        ROOT / "pets" / "mia" / "memes" / "bravo" / "mia_bravo_02.webp",
        ROOT / "pets" / "mia" / "memes" / "observando" / "mia_observando_01.webp",
        ROOT / "pets" / "mia" / "memes" / "triste" / "mia_triste_01.webp",
        ROOT / "pets" / "zuric" / "memes" / "feliz" / "zuric_feliz_01.webp",
        ROOT / "pets" / "zuric" / "memes" / "bravo" / "zuric_bravo_01.webp",
        ROOT / "pets" / "zuric" / "memes" / "assustado" / "zuric_assustado_02.webp",
        ROOT / "pets" / "zuric" / "memes" / "trabalhando" / "zuric_trabalhando_01.webp",
    ]
    vitrine = QImage(4 * 296, 2 * 296, QImage.Format_ARGB32)
    vitrine.fill(QColor("#0b0714"))
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

    # Mia
    (pets_dir / "mia.json").write_text(json.dumps(MIA_JSON, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mia_dir = pets_dir / "mia"
    mia_dir.mkdir(exist_ok=True)
    (mia_dir / "recadinhos.txt").write_text(MIA_RECADINHOS, encoding="utf-8")
    (mia_dir / "recadinhos_tristes.txt").write_text(MIA_TRISTES, encoding="utf-8")
    (mia_dir / "cartazes.txt").write_text(MIA_CARTAZES, encoding="utf-8")
    ap_mia = aparencia_de(MIA_JSON["aparencia"])
    sheet_mia = mia_dir / "sprites" / "_sheet.webp"
    if not extrair_sprites_da_folha(sheet_mia, mia_dir / "sprites"):
        for emo in list(EYE_SHAPES.keys()) + ["dormindo"]:
            gerar_sprite_expressao_webp(mia_dir / "sprites" / f"{emo}.webp", ap_mia, emo)
        gerar_sprite_expressao_webp(mia_dir / "sprites" / "carinho.webp", ap_mia, "feliz", carinho=True)
    _CACHE_SPRITES.clear()

    for emo, lista in MEMES_MIA.items():
        pasta_emo = mia_dir / "memes" / emo
        if pasta_emo.exists():
            for antigo in pasta_emo.glob("*.webp"):
                antigo.unlink()
        for nome_arq, legenda, cor, prop in lista:
            gerar_meme_webp(pasta_emo / f"{nome_arq}.webp", ap_mia, emo, legenda, cor, prop)

    # Zuric
    (pets_dir / "zuric.json").write_text(json.dumps(ZURIC_JSON, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    zuric_dir = pets_dir / "zuric"
    zuric_dir.mkdir(exist_ok=True)
    (zuric_dir / "recadinhos.txt").write_text(ZURIC_RECADINHOS, encoding="utf-8")
    (zuric_dir / "recadinhos_tristes.txt").write_text(ZURIC_TRISTES, encoding="utf-8")
    (zuric_dir / "cartazes.txt").write_text(ZURIC_CARTAZES, encoding="utf-8")
    ap_zuric = aparencia_de(ZURIC_JSON["aparencia"])
    sheet_zuric = zuric_dir / "sprites" / "_sheet.webp"
    if not extrair_sprites_da_folha(sheet_zuric, zuric_dir / "sprites"):
        for emo in list(EYE_SHAPES.keys()) + ["dormindo"]:
            gerar_sprite_expressao_webp(zuric_dir / "sprites" / f"{emo}.webp", ap_zuric, emo)
        gerar_sprite_expressao_webp(zuric_dir / "sprites" / "carinho.webp", ap_zuric, "feliz", carinho=True)
    _CACHE_SPRITES.clear()

    for emo, lista in MEMES_ZURIC.items():
        pasta_emo = zuric_dir / "memes" / emo
        if pasta_emo.exists():
            for antigo in pasta_emo.glob("*.webp"):
                antigo.unlink()
        for nome_arq, legenda, cor, prop in lista:
            gerar_meme_webp(pasta_emo / f"{nome_arq}.webp", ap_zuric, emo, legenda, cor, prop)
    gerar_bolinha_papel_webp(zuric_dir / "bolinha_papel.webp", "#00f0ff", "NERF!")

    if len(sys.argv) > 1:
        gerar_preview(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
