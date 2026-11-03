"""
DIÁRIO DO PET - painel local com o histórico de humor (lido de `timeline.csv` + sessão atual)
e a vitrine de conquistas (`Conquistas`).
"""

import csv
from collections import Counter

from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .. import config

ESTILO_DIARIO = """
QDialog { background: #0c1f13; color: #dfffe6; }
QScrollArea, QWidget#conteudo, QWidget#qt_scrollarea_viewport { background: #0c1f13; border: none; }
QLabel { color: #b9f5c8; font-size: 12px; }
QLabel#titulo { color: #63e56f; font: bold 18px 'Consolas'; }
QLabel#sub { color: #6f9c7b; font-size: 11px; }
QGroupBox { color: #63e56f; font: bold 12px; border: 1px solid #24402c;
            border-radius: 8px; margin-top: 12px; padding: 10px 8px 6px 8px; }
QProgressBar { background: #17201a; border: 1px solid #2c5236; border-radius: 4px;
               text-align: center; color: #dfffe6; height: 16px; }
QProgressBar::chunk { background: #2c8a40; }
QPushButton { background: #2c8a40; color: #dfffe6; border: 1px solid #63e56f;
              border-radius: 6px; padding: 6px 16px; font-weight: bold; }
"""


def historico_humor(timeline_path, emocoes_sessao=None):
    """Soma a contagem de minutos por emoção em `timeline.csv` mais o acumulador da sessão."""
    contagem = Counter()
    try:
        with open(timeline_path, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                em = (row.get("emocao") or "").strip().lower()
                if em:
                    contagem[em] += 1
    except OSError:
        pass
    if isinstance(emocoes_sessao, dict):
        for em, segs in emocoes_sessao.items():
            if isinstance(segs, (int, float)) and segs > 0:
                contagem[em] += max(1, int(round(segs / 60.0)))
    return dict(contagem)


class DiarioPanel(QDialog):
    """Painel do Diário do Pet: mostra a distribuição de humor e as conquistas desbloqueadas."""

    def __init__(self, nome_pet, timeline_path, conquistas, emocoes_sessao=None, parent=None):
        """Monta as seções de Histórico de Humor e Conquistas."""
        super().__init__(parent)
        self.setWindowTitle(f"Diário de {nome_pet}")
        self.setStyleSheet(ESTILO_DIARIO)
        self.resize(520, 600)

        outer = QVBoxLayout(self)
        titulo = QLabel(f"DIÁRIO E CONQUISTAS · {nome_pet.upper()}")
        titulo.setObjectName("titulo")
        outer.addWidget(titulo)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        conteudo = QWidget()
        conteudo.setObjectName("conteudo")
        layout = QVBoxLayout(conteudo)

        # 1. Histórico de Humor
        grupo_humor = QGroupBox("Histórico de Humor")
        l_humor = QVBoxLayout(grupo_humor)
        humor = historico_humor(timeline_path, emocoes_sessao)
        total_humor = sum(humor.values())
        if total_humor == 0:
            vazio = QLabel("Ainda começando a registrar momentos com você nesta sessão!")
            vazio.setObjectName("sub")
            l_humor.addWidget(vazio)
        else:
            for emocao, qtd in sorted(humor.items(), key=lambda x: -x[1]):
                linha = QHBoxLayout()
                nome_em = config.EMOTION_NAMES.get(emocao, emocao.upper())
                linha.addWidget(QLabel(f"{nome_em}:"), 1)
                barra = QProgressBar()
                barra.setRange(0, max(1, total_humor))
                barra.setValue(qtd)
                barra.setFormat(f"{qtd} min ({int(round(100 * qtd / total_humor))}%)")
                linha.addWidget(barra, 2)
                l_humor.addLayout(linha)
        layout.addWidget(grupo_humor)

        # 2. Conquistas
        lista_conq = conquistas.resumo()
        desb_qtd = sum(1 for c in lista_conq if c["desbloqueada"])
        grupo_conq = QGroupBox(f"Conquistas ({desb_qtd}/{len(lista_conq)})")
        l_conq = QVBoxLayout(grupo_conq)
        for item in lista_conq:
            icone = "🏆" if item["desbloqueada"] else "🔒"
            progresso = f"{min(item['atual'], item['meta'])}/{item['meta']}"
            lbl = QLabel(f"{icone} <b>{item['titulo']}</b> ({progresso}) — {item['descricao']}")
            lbl.setWordWrap(True)
            l_conq.addWidget(lbl)
        layout.addWidget(grupo_conq)
        layout.addStretch(1)

        scroll.setWidget(conteudo)
        outer.addWidget(scroll, 1)

        botoes = QHBoxLayout()
        botoes.addStretch(1)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.accept)
        botoes.addWidget(fechar)
        outer.addLayout(botoes)
