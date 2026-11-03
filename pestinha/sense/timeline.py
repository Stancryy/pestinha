"""
TIMELINE - uma linha por minuto da sua rotina, para o futuro LSTM.

Grava SÓ categorias e contagens (nunca título de janela, nome de site ou
conteúdo) em memory/timeline.csv. Fica no seu computador; o botão
"Apagar histórico" da tela inicial remove o arquivo.

Colunas:
    inicio          início do minuto (ISO, hora local)
    dia_semana      0 = segunda ... 6 = domingo
    minuto_do_dia   0..1439
    atividade       categoria dominante no minuto (PROGRAMMING, BROWSING, AWAY...)
    ausente         fração do minuto ausente (0..1)
    ocioso          fração sem teclado/mouse por mais de 5 s
    digitando       fração com teclado ativo (mouse parado)
    trocas_app      quantas vezes trocou de programa
    sessao_min      minutos desde que você voltou/começou
    interacoes      cutucadas + arrastes + segundos de carinho no pet
    emocao          emoção dominante do pet no minuto
"""

from ..log import log
import csv
import time
from collections import Counter
from datetime import datetime

COLUMNS = [
    "inicio", "dia_semana", "minuto_do_dia", "atividade", "ausente", "ocioso",
    "digitando", "trocas_app", "sessao_min", "interacoes", "emocao",
]

MIN_SECONDS = 30.0          # minuto parcial menor que isso (ao fechar) é descartado


class TimelineRecorder:
    """Registra a rotina: uma linha por minuto (atividade, ocioso, emoções). Nunca grava títulos de janelas."""
    def __init__(self, path, coletando=lambda: True):
        """Guarda o arquivo e a função que diz se a rotina está ligada (desligada = nada é acumulado)."""
        self.path = path
        self.coletando = coletando          # False: a rotina está desligada, nada é acumulado
        self._start_minute()

    def discard(self):
        """Apaga o histórico gravado e o minuto que ainda estava em RAM: nada disso volta a ser gravado."""
        self._start_minute()
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass

    def _start_minute(self):
        """Começa a contar um novo minuto, zerando os acumuladores."""
        now = datetime.now()
        self.minute = now.replace(second=0, microsecond=0)
        self.activity = Counter()
        self.emotion = Counter()
        self.seconds = 0.0
        self.away = self.idle = self.typing = 0.0
        self.switches = 0
        self.interactions = 0.0
        self.session_seconds = 0.0
        self.last = time.monotonic()

    # ---------------- coleta ----------------

    def observe(self, activity, idle_seconds, events, session_seconds, typing):
        """Chamar junto com os sensores (a cada ~0,5 s)."""
        now = time.monotonic()
        dt = min(5.0, max(0.0, now - self.last))
        self.last = now

        if datetime.now().replace(second=0, microsecond=0) != self.minute:
            self.flush()
            self._start_minute()
            return

        self.seconds += dt
        self.activity[activity] += dt
        if activity == "AWAY":
            self.away += dt
        if idle_seconds > 5.0:
            self.idle += dt
        if typing:
            self.typing += dt
        self.switches += events.count("APP_CHANGED")
        self.session_seconds = session_seconds

    def note_emotion(self, emotion, dt):
        """Soma o tempo que o pet passou numa emoção, neste minuto."""
        if self.coletando():
            self.emotion[emotion] += dt

    def note_interaction(self, amount=1.0):
        """Conta uma interação sua com o pet (cutucada, carinho...) neste minuto."""
        if self.coletando():
            self.interactions += amount

    # ---------------- gravação ----------------

    def flush(self):
        """Grava o minuto no arquivo se ele tiver tempo suficiente (minutos incompletos são descartados)."""
        if self.seconds < MIN_SECONDS or not self.activity:
            return
        s = self.seconds
        row = [
            self.minute.isoformat(timespec="minutes"),
            self.minute.weekday(),
            self.minute.hour * 60 + self.minute.minute,
            self.activity.most_common(1)[0][0],
            round(self.away / s, 3),
            round(self.idle / s, 3),
            round(self.typing / s, 3),
            self.switches,
            round(self.session_seconds / 60.0, 1),
            round(self.interactions, 1),
            self.emotion.most_common(1)[0][0] if self.emotion else "",
        ]
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            new = not self.path.exists()
            with open(self.path, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if new:
                    writer.writerow(COLUMNS)
                writer.writerow(row)
        except OSError as error:
            log(f"[timeline] não gravou: {error}")

    def close(self):
        """Grava o minuto que estava em andamento ao fechar o app."""
        self.flush()
        self._start_minute()


def count_rows(path):
    """Quantas linhas (minutos) já estão gravadas na rotina."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return max(0, sum(1 for _ in f) - 1)
    except OSError:
        return 0


def fator_ciclo_rotina(path, hora_atual=None):
    """
    Calcula o fator de energia (0.72 a 1.15) adaptativo à rotina aprendida em `timeline.csv`.
    Não usa horários fixos: aprende em quais horas do dia você costuma estar ativo ou ausente.
    Com menos de 10 minutos gravados, devolve 1.0 (neutro).
    """
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            por_hora = {h: [0, 0] for h in range(24)}
            total_linhas = 0
            for row in reader:
                try:
                    minuto_dia = int(row.get("minuto_do_dia", -1))
                    hora = (minuto_dia // 60) % 24 if minuto_dia >= 0 else 0
                    ativ = (row.get("atividade") or "").strip().upper()
                    ausente = float(row.get("ausente", 0.0))
                except (TypeError, ValueError):
                    continue
                por_hora[hora][1] += 1
                if ativ != "AWAY" and ausente < 0.5:
                    por_hora[hora][0] += 1
                total_linhas += 1
    except OSError:
        return 1.0
    if total_linhas < 10:
        return 1.0
    hora_ref = datetime.now().hour if hora_atual is None else int(hora_atual) % 24
    ativos_hora, total_hora = por_hora[hora_ref]
    if total_hora == 0:
        return 1.0
    taxa_hora = ativos_hora / total_hora
    total_ativos = sum(v[0] for v in por_hora.values())
    media_geral = total_ativos / max(1, total_linhas)
    if media_geral <= 0.05:
        return 1.0
    if taxa_hora < media_geral * 0.65:
        return 0.72
    if taxa_hora > media_geral * 1.15:
        return 1.15
    return 1.0


def _ignorar_count_rows(path):
    """Quantas linhas (minutos) já estão gravadas na rotina."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return max(0, sum(1 for _ in f) - 1)
    except OSError:
        return 0
