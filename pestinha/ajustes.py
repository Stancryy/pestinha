"""
AJUSTES - todos os números que dão o jeito do pet, em um lugar só.

Mudar um valor aqui muda o comportamento. Ao importar, `validar()` confere os
tipos e os limites de cada valor e, se algo estiver fora, levanta ValueError
com a lista completa dos problemas (o programa não sobe com ajuste errado).

Os perfis de tempo (teste e normal) ficam em `pestinha/config.py`.
"""

# ---------------------------------------------------------------------------
# Interação com o mouse
# ---------------------------------------------------------------------------
COOLDOWN_CUTUCADA = 0.25        # s entre cutucadas que contam
TEMPO_MAX_CUTUCADA_MS = 350     # ms: clique mais longo que isso não é cutucada
DISTANCIA_INICIO_ARRASTE = 5    # px que o mouse precisa andar para virar arraste
VELOCIDADE_ARREMESSO = 700      # px/s: soltar mais rápido que isso é arremesso
JANELA_CARINHO = 1.2            # s analisados para reconhecer o carinho
TROCAS_CARINHO = 3              # trocas de direção em JANELA_CARINHO para ser carinho
DESLOCAMENTO_CARINHO = 60       # px percorridos em JANELA_CARINHO para ser carinho
DURACAO_CARINHO = 0.4           # s que o carinho dura depois do último esfregão

# ---------------------------------------------------------------------------
# Batidas e reflexos
# ---------------------------------------------------------------------------
BATIDA_FORTE = 1500             # px/s: batida que ele sente
BATIDA_TONTA = 2000             # px/s: batida que deixa ele tonto
DURACAO_TONTURA = 1.6           # s olhando em volta depois de uma batida tonta
INTERVALO_BATIDA = 0.6          # s: quiques da mesma batida não contam de novo
ATIVIDADE_MINIMA_VOO = 4.0      # Hz: abaixo disso o reflexo de voo é só alegria
SILENCIO_MOUSE = 0.4            # s sem o cursor andar para o teclado contar

# ---------------------------------------------------------------------------
# Cutucada e a resposta medida na rede
# ---------------------------------------------------------------------------
ESPERA_MEDIDA_CUTUCADA = 0.5    # s depois da cutucada em que se mede a resposta
HZ_RESPOSTA_CHEIA = 6.0         # aumento de CHEER que vale resposta 1,0
RESPOSTA_MINIMA = 0.12          # abaixo disso ele só pisca e olha
RECOMPENSA_CARINHO = 1.0        # recompensa por segundo de carinho (aprendizado)
PUNICAO_DISPENSA = -0.6         # recompensa negativa depois de dispensar
DISPENSA_RAPIDA = 3.0           # s: fechou tão rápido assim = dispensa "na cara"
PENALIDADE_DISPENSA = 1.0       # s em que a dispensa pesa no aprendizado

# ---------------------------------------------------------------------------
# Física do corpo (núcleo)
# ---------------------------------------------------------------------------
GRAVIDADE = 2200.0              # px/s² do pet e da bolinha
QUICA = 0.35                    # quanto da velocidade sobra depois de quicar
ATRITO_CHAO = 6.0               # 1/s
ARRASTO_AR = 0.15               # 1/s
ARRASTO_GIRO_AR = 0.8           # 1/s
MOLA_ENDIREITAR = 60.0          # força que ajeita o corpo tombado
AMORTECIMENTO_ENDIREITAR = 9.0
GIRO_MAXIMO = 1000.0            # graus/s
BOTOES_JANELA = 150             # px à direita da janela onde ele não pousa

# ---------------------------------------------------------------------------
# Bolinha
# ---------------------------------------------------------------------------
RAIO_BOLINHA = 18               # px
PERTO_BOLINHA = 170             # px: perto dele
LONGE_BOLINHA = 420             # px: longe o bastante para ter sido "levada"
MEMORIA_SOLTURA = 4.0           # s: depois de soltar, ainda conta como "você mexeu"
REPOUSO_BATIDA = 0.45           # quanto da velocidade sobra depois de bater
INTERVALO_CURSOR = 0.25         # s: o cursor não chuta a bolinha de novo logo depois

# ---------------------------------------------------------------------------
# Brincadeira
# ---------------------------------------------------------------------------
ALCANCE_BRINCADEIRA = 240       # px: a bolinha precisa estar perto dele
TEMPO_VOO_ARREMESSO = 0.7       # s de voo do arremesso até o cursor
INTERVALO_BRINCADEIRA = (2.5, 5.0)   # s entre tentativas de brincar
INTERVALO_PAPEL = 0.45          # s entre bolinhas de papel na revolução

# ---------------------------------------------------------------------------
# Protesto (raiva) e tristeza
# ---------------------------------------------------------------------------
LIMITES_ESTAGIO = [0.25, 0.5, 0.75, 1.0]   # insatisfação para entrar em 1, 2, 3, 4
HISTERESE = 0.12                # para sair de um estágio, cair isso abaixo
INSATISFACAO_MAXIMA = 1.3
ALIVIO_CARINHO = 0.3            # por segundo de carinho
REPRESSAO = 0.15                # cartaz arrancado à força
CRESCIMENTO_BANDEIRA = 0.25     # cada revolução: bandeira 25% maior
ESCALA_MAXIMA = 2.0
TEMPO_CARTAZ_FIM = 3.5          # s que o cartaz de fim (acordo ou volto) fica

# ---------------------------------------------------------------------------
# Travessuras
# ---------------------------------------------------------------------------
TAMANHO_MEME = 230              # px, lado maior de um meme entregue
TAMANHO_MEME_CANTO = 120        # px, meme pequeno de revolta no cantinho

# ---------------------------------------------------------------------------
# Fogos de artifício
# ---------------------------------------------------------------------------
TAMANHO_JANELA_FOGOS = 420      # px
TEMPO_FOGUETE = 0.55            # s que o foguete leva para subir
GRAVIDADE_FOGOS = 260.0         # px/s² das partículas
VIDA_PARTICULA = 1.8            # s
ESPERA_FOGOS = 40.0             # s entre um fogo e outro
EUFORIA_MAXIMA = 1.5

# ---------------------------------------------------------------------------
# Mesa (notebook)
# ---------------------------------------------------------------------------
FOCO_MAXIMO_HZ = 6.0           # taxa da população FOCUS que vale foco 1,0
FRACAO_ESCONDIDA_NOTEBOOK = 0.45  # fração da altura do pet escondida atrás da tampa do notebook
ALCANCE_NOTEBOOK = 300          # px: arrastar o notebook além disso faz o pet levantar e reagir
INSATISFACAO_NOTEBOOK = 0.35    # quanto a insatisfação sobe quando ele é arrancado da mesa (máximo 1,3)
PEDIDO_VALIDADE_S = 60.0        # s em que um pedido para trabalhar ainda vale
JANELA_PEDIDOS_S = 900.0        # s em que os pedidos contam para a frustração

FELIZ_APOS_CARINHO = 1.5        # s com os olhinhos fechados de felicidade depois do último carinho

# ---------------------------------------------------------------------------
# DECISÕES PELA REDE: cada uma é um neurônio motor. O limiar é a taxa de disparo
# (Hz) dele; a frequência de uma travessura ou de uma bolinha é a taxa vezes o ganho.
# ---------------------------------------------------------------------------
LIMIAR_SENTAR_HZ = 6.0          # SENTAR acima disso: senta
LIMIAR_LEVANTAR_HZ = 3.0        # SENTAR abaixo disso: levanta (histerese)
LIMIAR_FUGA_HZ = 2.0            # FUGIR acima disso enche a vontade de fugir; abaixo, ela vaza
CARGA_FUGA_HZ_S = 300.0         # Hz·s acima do limiar para a vontade encher (bravo: ~30 s; entediado: ~50 s)
LIMIAR_CANTO_HZ = 3.0           # CANTO acima disso: vai para o cantinho
GANHO_TRAVESSURA = 0.002        # travessuras por segundo, por Hz do motor TRAVESSURA
GANHO_CARTAZ = 0.5              # cartazes por segundo, por Hz do motor CARTAZ
GANHO_PAPEL = 0.05              # bolinhas de papel por segundo, por Hz do motor PAPEL

# ---------------------------------------------------------------------------
# Rosto e janela
# ---------------------------------------------------------------------------
LADO_JANELA_PET = 200         # px da janela transparente do corpo
ZZZ_QUANTIDADE = 3
ZZZ_PERIODO = 2.4               # s que cada Z leva para subir e sumir
INTERVALO_QUADRO_ATIVO_MS = 16  # ms entre quadros em movimento (~60 fps)
INTERVALO_QUADRO_PARADO_MS = 50 # ms entre quadros parado em repouso (~20 fps)
INTERVALO_QUADRO_DORMINDO_MS = 200  # ms entre quadros dormindo (~5 fps)
LIMIAR_CPU_ALTA = 85.0          # % de CPU a partir do qual o pet sua (quando reagir_hardware ligado)
LIMIAR_RAM_ALTA = 88.0          # % de RAM a partir do qual o pet fica apertado (quando reagir_hardware ligado)
POMODORO_FOCO_MIN = 25          # minutos do ciclo de foco do Pomodoro
POMODORO_PAUSA_MIN = 5          # minutos de pausa sugerida após o Pomodoro
INTERVALO_LEMBRETE_MIN = 45     # minutos entre lembretes opcionais de água e postura

# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

# nome: (tipo, mínimo, máximo) para números; listas e tuplas têm regra própria
_LIMITES = {
    "COOLDOWN_CUTUCADA": (float, 0.0, 5.0),
    "TEMPO_MAX_CUTUCADA_MS": (int, 50, 2000),
    "DISTANCIA_INICIO_ARRASTE": (int, 0, 100),
    "VELOCIDADE_ARREMESSO": (float, 100.0, 5000.0),
    "JANELA_CARINHO": (float, 0.1, 10.0),
    "TROCAS_CARINHO": (int, 1, 20),
    "DESLOCAMENTO_CARINHO": (float, 0.0, 1000.0),
    "DURACAO_CARINHO": (float, 0.0, 10.0),
    "BATIDA_FORTE": (float, 100.0, 10000.0),
    "BATIDA_TONTA": (float, 100.0, 10000.0),
    "DURACAO_TONTURA": (float, 0.0, 10.0),
    "INTERVALO_BATIDA": (float, 0.0, 10.0),
    "ATIVIDADE_MINIMA_VOO": (float, 0.0, 100.0),
    "SILENCIO_MOUSE": (float, 0.0, 10.0),
    "ESPERA_MEDIDA_CUTUCADA": (float, 0.0, 5.0),
    "HZ_RESPOSTA_CHEIA": (float, 0.1, 100.0),
    "RESPOSTA_MINIMA": (float, 0.0, 1.0),
    "RECOMPENSA_CARINHO": (float, 0.0, 10.0),
    "PUNICAO_DISPENSA": (float, -10.0, 0.0),
    "DISPENSA_RAPIDA": (float, 0.0, 60.0),
    "PENALIDADE_DISPENSA": (float, 0.0, 60.0),
    "GRAVIDADE": (float, 0.0, 100000.0),
    "QUICA": (float, 0.0, 1.0),
    "ATRITO_CHAO": (float, 0.0, 100.0),
    "ARRASTO_AR": (float, 0.0, 100.0),
    "ARRASTO_GIRO_AR": (float, 0.0, 100.0),
    "MOLA_ENDIREITAR": (float, 0.0, 10000.0),
    "AMORTECIMENTO_ENDIREITAR": (float, 0.0, 1000.0),
    "GIRO_MAXIMO": (float, 0.0, 100000.0),
    "BOTOES_JANELA": (int, 0, 1000),
    "RAIO_BOLINHA": (int, 4, 200),
    "PERTO_BOLINHA": (int, 1, 2000),
    "LONGE_BOLINHA": (int, 1, 5000),
    "MEMORIA_SOLTURA": (float, 0.0, 60.0),
    "REPOUSO_BATIDA": (float, 0.0, 1.0),
    "INTERVALO_CURSOR": (float, 0.0, 10.0),
    "ALCANCE_BRINCADEIRA": (int, 1, 5000),
    "TEMPO_VOO_ARREMESSO": (float, 0.05, 10.0),
    "INTERVALO_PAPEL": (float, 0.05, 60.0),
    "HISTERESE": (float, 0.0, 1.0),
    "INSATISFACAO_MAXIMA": (float, 0.1, 10.0),
    "ALIVIO_CARINHO": (float, 0.0, 10.0),
    "REPRESSAO": (float, 0.0, 10.0),
    "CRESCIMENTO_BANDEIRA": (float, 0.0, 10.0),
    "ESCALA_MAXIMA": (float, 1.0, 10.0),
    "TEMPO_CARTAZ_FIM": (float, 0.0, 60.0),
    "TAMANHO_MEME": (int, 16, 2000),
    "TAMANHO_MEME_CANTO": (int, 16, 2000),
    "TAMANHO_JANELA_FOGOS": (int, 100, 2000),
    "TEMPO_FOGUETE": (float, 0.05, 10.0),
    "GRAVIDADE_FOGOS": (float, 0.0, 100000.0),
    "VIDA_PARTICULA": (float, 0.05, 60.0),
    "ESPERA_FOGOS": (float, 0.0, 3600.0),
    "EUFORIA_MAXIMA": (float, 0.1, 10.0),
    "FOCO_MAXIMO_HZ": (float, 0.1, 500.0),
    "FRACAO_ESCONDIDA_NOTEBOOK": (float, 0.0, 0.9),
    "ALCANCE_NOTEBOOK": (int, 50, 2000),
    "INSATISFACAO_NOTEBOOK": (float, 0.0, 1.3),
    "PEDIDO_VALIDADE_S": (float, 1.0, 600.0),
    "JANELA_PEDIDOS_S": (float, 60.0, 86400.0),
    "FELIZ_APOS_CARINHO": (float, 0.0, 30.0),
    "LIMIAR_SENTAR_HZ": (float, 0.0, 200.0),
    "LIMIAR_LEVANTAR_HZ": (float, 0.0, 200.0),
    "LIMIAR_FUGA_HZ": (float, 0.0, 200.0),
    "CARGA_FUGA_HZ_S": (float, 0.1, 10000.0),
    "LIMIAR_CANTO_HZ": (float, 0.0, 200.0),
    "GANHO_TRAVESSURA": (float, 0.0, 1.0),
    "GANHO_CARTAZ": (float, 0.0, 1.0),
    "GANHO_PAPEL": (float, 0.0, 1.0),
    "LADO_JANELA_PET": (int, 100, 1000),
    "ZZZ_QUANTIDADE": (int, 0, 20),
    "ZZZ_PERIODO": (float, 0.1, 60.0),
    "INTERVALO_QUADRO_ATIVO_MS": (int, 8, 50),
    "INTERVALO_QUADRO_PARADO_MS": (int, 16, 200),
    "INTERVALO_QUADRO_DORMINDO_MS": (int, 50, 1000),
    "LIMIAR_CPU_ALTA": (float, 10.0, 100.0),
    "LIMIAR_RAM_ALTA": (float, 10.0, 100.0),
    "POMODORO_FOCO_MIN": (int, 1, 180),
    "POMODORO_PAUSA_MIN": (int, 1, 60),
    "INTERVALO_LEMBRETE_MIN": (int, 5, 240),
}


def validar():
    """Confere tipo e limite de cada ajuste. Levanta ValueError com todos os problemas."""
    erros = []
    atuais = globals()
    for nome, (tipo, minimo, maximo) in _LIMITES.items():
        valor = atuais.get(nome)
        if valor is None:
            erros.append(f"{nome}: falta o ajuste")
            continue
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            erros.append(f"{nome}: deveria ser número, veio {type(valor).__name__}")
            continue
        if tipo is int and not float(valor).is_integer():
            erros.append(f"{nome}: deveria ser inteiro, veio {valor}")
        if not (minimo <= valor <= maximo):
            erros.append(f"{nome}: {valor} está fora de [{minimo}, {maximo}]")
    for nome in ("INTERVALO_BRINCADEIRA",):
        par = atuais[nome]
        if not (isinstance(par, tuple) and len(par) == 2 and 0 < par[0] <= par[1] <= 600):
            erros.append(f"{nome}: deveria ser (mínimo, máximo) com 0 < mínimo <= máximo <= 600")
    limites = atuais["LIMITES_ESTAGIO"]
    if not (len(limites) == 4 and all(0 < a < b for a, b in zip(limites, limites[1:]))):
        erros.append("LIMITES_ESTAGIO: deveria ter 4 valores crescentes e positivos")
    if erros:
        raise ValueError("ajustes inválidos:\n  " + "\n  ".join(erros))


VALORES_PADRAO = {nome: globals()[nome] for nome in _LIMITES}


def valores_atuais():
    """Devolve um dicionário com os valores numéricos atuais de todos os ajustes em `_LIMITES`."""
    atuais = globals()
    return {nome: atuais[nome] for nome in _LIMITES}


def aplicar_ajustes(novos):
    """Aplica um dicionário de ajustes validando tipo e limitando a `[minimo, maximo]` de `_LIMITES`."""
    if not isinstance(novos, dict):
        return valores_atuais()
    atuais = globals()
    for nome, valor in novos.items():
        if nome not in _LIMITES or isinstance(valor, bool) or not isinstance(valor, (int, float)):
            continue
        tipo, minimo, maximo = _LIMITES[nome]
        limitado = max(minimo, min(maximo, valor))
        atuais[nome] = int(round(limitado)) if tipo is int else float(limitado)
    validar()
    return valores_atuais()


def carregar_ajustes(caminho):
    """Lê `memory/ajustes.json` (se existir) e aplica apenas valores válidos dentro de `_LIMITES`."""
    from .store import read_json
    salvos = read_json(caminho, default=None)
    if isinstance(salvos, dict):
        return aplicar_ajustes(salvos)
    return valores_atuais()


def salvar_ajustes(caminho, novos):
    """Aplica `novos` e grava os ajustes personalizados em `memory/ajustes.json`."""
    from .store import write_json
    atuais = aplicar_ajustes(novos)
    write_json(caminho, atuais, indent=2)
    return atuais


def restaurar_padroes(caminho=None):
    """Restaura todos os números de `_LIMITES` para os valores originais de fábrica."""
    atuais = globals()
    for nome, valor in VALORES_PADRAO.items():
        atuais[nome] = valor
    if caminho is not None:
        try:
            from pathlib import Path
            Path(caminho).unlink(missing_ok=True)
        except OSError:
            pass
    validar()
    return valores_atuais()


validar()
