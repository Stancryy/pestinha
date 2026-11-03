"""
FERRAMENTAS UI - diálogos de Ajustes Finos (`ajustes.py`), Editor de Programas (`ACTIVITY_APPS`)
e Assistente (Wizard) de Criação de Personagem.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import ajustes, config
from ..sense import senses

ESTILO_DIALOGO = """
QDialog { background: #0c1f13; color: #dfffe6; }
QScrollArea, QWidget#conteudo, QWidget#qt_scrollarea_viewport { background: #0c1f13; border: none; }
QLabel { color: #b9f5c8; font-size: 12px; }
QLabel#titulo { color: #63e56f; font: bold 18px 'Consolas'; }
QLabel#dica { color: #6f9c7b; font-size: 11px; }
QGroupBox { color: #63e56f; font: bold 12px; border: 1px solid #24402c;
            border-radius: 8px; margin-top: 12px; padding: 10px 8px 6px 8px; }
QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #17201a; color: #dfffe6; border: 1px solid #2c5236; border-radius: 4px; padding: 4px 6px;
}
QPushButton { background: #17201a; color: #dfffe6; border: 1px solid #2c5236;
              border-radius: 6px; padding: 6px 14px; font-size: 12px; }
QPushButton#primario { background: #2c8a40; border-color: #63e56f; font-weight: bold; }
QPushButton:hover { border-color: #63e56f; }
"""


class AjustesDialog(QDialog):
    """Tela para editar os números de `pestinha/ajustes.py` respeitando `_LIMITES`."""

    salvo = Signal(dict)

    def __init__(self, paths, parent=None):
        """Monta os campos numéricos validados por `ajustes._LIMITES`."""
        super().__init__(parent)
        self.paths = paths
        self.setWindowTitle(f"{config.APP_NOME} · Ajustes Finos")
        self.setStyleSheet(ESTILO_DIALOGO)
        self.resize(560, 640)

        ajustes.carregar_ajustes(self.paths.ajustes)
        atuais = ajustes.valores_atuais()
        self.campos = {}
        self.linhas = {}

        outer = QVBoxLayout(self)
        titulo = QLabel("AJUSTES FINOS DE FÍSICA, REDE E TEMPO")
        titulo.setObjectName("titulo")
        outer.addWidget(titulo)

        filtro_row = QHBoxLayout()
        filtro_row.addWidget(QLabel("Filtrar ajuste:"))
        self.filtro_edit = QLineEdit()
        self.filtro_edit.setPlaceholderText("Ex.: GRAVIDADE, CARINHO, SENTAR, QUADRO...")
        self.filtro_edit.textChanged.connect(self._filtrar)
        filtro_row.addWidget(self.filtro_edit, 1)
        outer.addLayout(filtro_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        conteudo = QWidget()
        conteudo.setObjectName("conteudo")
        form = QFormLayout(conteudo)
        form.setSpacing(6)

        for nome, (tipo, minimo, maximo) in ajustes._LIMITES.items():
            rotulo = QLabel(f"{nome}  [{minimo} .. {maximo}]")
            if tipo is int:
                campo = QSpinBox()
                campo.setRange(int(minimo), int(maximo))
                campo.setValue(int(atuais[nome]))
            else:
                campo = QDoubleSpinBox()
                campo.setDecimals(4 if maximo <= 2.0 else 2)
                campo.setRange(float(minimo), float(maximo))
                campo.setSingleStep(0.05 if maximo <= 2.0 else 1.0)
                campo.setValue(float(atuais[nome]))
            self.campos[nome] = campo
            self.linhas[nome] = (rotulo, campo)
            form.addRow(rotulo, campo)

        scroll.setWidget(conteudo)
        outer.addWidget(scroll, 1)

        botoes = QHBoxLayout()
        restaurar = QPushButton("Restaurar padrões")
        restaurar.clicked.connect(self._restaurar)
        botoes.addWidget(restaurar)
        botoes.addStretch(1)
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        botoes.addWidget(cancelar)
        salvar = QPushButton("Salvar")
        salvar.setObjectName("primario")
        salvar.clicked.connect(self._salvar)
        botoes.addWidget(salvar)
        outer.addLayout(botoes)

    def _filtrar(self, texto):
        """Mostra apenas as linhas cujo nome contém o texto buscado."""
        termo = (texto or "").strip().upper()
        for nome, (rotulo, campo) in self.linhas.items():
            visivel = not termo or termo in nome
            rotulo.setVisible(visivel)
            campo.setVisible(visivel)

    def coletar_valores(self):
        """Lê os valores atuais dos campos da tela."""
        out = {}
        for nome, (tipo, _min, _max) in ajustes._LIMITES.items():
            val = self.campos[nome].value()
            out[nome] = int(val) if tipo is int else float(val)
        return out

    def _restaurar(self):
        """Restaura os valores de fábrica em disco e nos campos."""
        padroes = ajustes.restaurar_padroes(self.paths.ajustes)
        for nome, valor in padroes.items():
            self.campos[nome].setValue(valor)
        self.salvo.emit(padroes)

    def _salvar(self):
        """Salva os valores em `memory/ajustes.json` e aplica imediatamente."""
        novos = ajustes.salvar_ajustes(self.paths.ajustes, self.coletar_valores())
        self.salvo.emit(novos)
        self.accept()


class AtividadesDialog(QDialog):
    """Editor visual da lista de programas por categoria (`ACTIVITY_APPS` / `memory/activities.json`)."""

    salvo = Signal(dict)

    def __init__(self, paths, parent=None):
        """Carrega as categorias atuais e cria um campo de texto por categoria."""
        super().__init__(parent)
        self.paths = paths
        self.setWindowTitle(f"{config.APP_NOME} · Programas e Atividades")
        self.setStyleSheet(ESTILO_DIALOGO)
        self.resize(540, 580)

        mapa = senses.carregar_atividades(self.paths.activities)
        self.editores = {}

        outer = QVBoxLayout(self)
        titulo = QLabel("PROGRAMAS POR ATIVIDADE")
        titulo.setObjectName("titulo")
        outer.addWidget(titulo)
        dica = QLabel(
            "Separe os nomes dos processos por vírgula (sem .exe, tudo em minúsculo). "
            "O pet olha apenas o nome do processo ativo, nunca o título da janela."
        )
        dica.setObjectName("dica")
        dica.setWordWrap(True)
        outer.addWidget(dica)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        conteudo = QWidget()
        conteudo.setObjectName("conteudo")
        self.form_layout = QVBoxLayout(conteudo)

        for categoria, apps in mapa.items():
            self._adicionar_bloco_categoria(categoria, apps)

        scroll.setWidget(conteudo)
        outer.addWidget(scroll, 1)

        nova_row = QHBoxLayout()
        self.nova_cat_edit = QLineEdit()
        self.nova_cat_edit.setPlaceholderText("Nova categoria (ex.: STUDYING)")
        nova_row.addWidget(self.nova_cat_edit, 1)
        btn_add = QPushButton("Adicionar categoria")
        btn_add.clicked.connect(self._criar_categoria)
        nova_row.addWidget(btn_add)
        outer.addLayout(nova_row)

        botoes = QHBoxLayout()
        restaurar = QPushButton("Restaurar padrão")
        restaurar.clicked.connect(self._restaurar_padrao)
        botoes.addWidget(restaurar)
        botoes.addStretch(1)
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        botoes.addWidget(cancelar)
        salvar = QPushButton("Salvar")
        salvar.setObjectName("primario")
        salvar.clicked.connect(self._salvar)
        botoes.addWidget(salvar)
        outer.addLayout(botoes)

    def _adicionar_bloco_categoria(self, categoria, apps):
        """Cria um grupo para editar os programas de `categoria`."""
        grupo = QGroupBox(categoria)
        layout = QVBoxLayout(grupo)
        editor = QPlainTextEdit(", ".join(apps))
        editor.setMaximumHeight(68)
        layout.addWidget(editor)
        self.editores[categoria] = editor
        self.form_layout.addWidget(grupo)

    def _criar_categoria(self):
        """Adiciona uma nova categoria personalizada na tela."""
        nome = self.nova_cat_edit.text().strip().upper()
        if not nome or nome in self.editores:
            return
        self._adicionar_bloco_categoria(nome, [])
        self.nova_cat_edit.clear()

    def coletar_mapa(self):
        """Monta o dicionário `{CATEGORIA: [apps...]}` a partir dos campos da tela."""
        out = {}
        for cat, editor in self.editores.items():
            itens = [p.strip().lower().removesuffix(".exe") for p in editor.toPlainText().replace("\n", ",").split(",")]
            limpos = [p for p in itens if p]
            if limpos:
                out[cat] = limpos
        return out

    def _restaurar_padrao(self):
        """Restaura `DEFAULT_ACTIVITY_APPS` nos campos e salva."""
        for cat, apps in senses.DEFAULT_ACTIVITY_APPS.items():
            if cat in self.editores:
                self.editores[cat].setPlainText(", ".join(apps))

    def _salvar(self):
        """Grava em `memory/activities.json` e atualiza `senses.ACTIVITY_APPS`."""
        mapa = senses.salvar_atividades(self.paths.activities, self.coletar_mapa())
        self.salvo.emit(mapa)
        self.accept()


class WizardPetDialog(QDialog):
    """Assistente (Wizard) para criar um novo personagem pela interface."""

    pet_criado = Signal(str)

    def __init__(self, paths, parent=None):
        """Campos de nome, temperamento, cores, formato e frases iniciais."""
        super().__init__(parent)
        self.paths = paths
        self.setWindowTitle(f"{config.APP_NOME} · Criar Novo Personagem")
        self.setStyleSheet(ESTILO_DIALOGO)
        self.resize(500, 620)

        outer = QVBoxLayout(self)
        titulo = QLabel("ASSISTENTE DE NOVO PERSONAGEM")
        titulo.setObjectName("titulo")
        outer.addWidget(titulo)

        form = QFormLayout()
        self.nome_edit = QLineEdit("Kira")
        self.id_edit = QLineEdit("kira")
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(1, 999999)
        self.seed_spin.setValue(108)

        self.temp_combo = QComboBox()
        for chave, rotulo in [("equilibrado", "Equilibrado"), ("calmo", "Calmo / Focado"), ("caotico", "Caótico / Bagunceiro")]:
            self.temp_combo.addItem(rotulo, chave)

        self.reacao_combo = QComboBox()
        for chave, rotulo in [("misto", "Misto (ora bravo, ora triste)"), ("bravo", "Bravo"), ("triste", "Triste")]:
            self.reacao_combo.addItem(rotulo, chave)

        self.formato_combo = QComboBox()
        for fmt in ("arredondado", "gatinho", "quadrado", "gota"):
            self.formato_combo.addItem(fmt, fmt)

        self.fundo_edit = QLineEdit("#2a1f2d")
        self.borda_edit = QLineEdit("#ff8da1")
        self.olho_edit = QLineEdit("#e0115f")
        self.boca_edit = QLineEdit("#ffebf0")

        self.recados_edit = QPlainTextEdit(
            "Oi! Já salvou o projeto hoje?\nFaz um cafuné aqui antes de compilar!\nHora de beber água!"
        )
        self.recados_edit.setMaximumHeight(90)

        form.addRow("Nome:", self.nome_edit)
        form.addRow("ID (nome do arquivo):", self.id_edit)
        form.addRow("Semente da rede (seed):", self.seed_spin)
        form.addRow("Temperamento:", self.temp_combo)
        form.addRow("Reação ao arrancar notebook:", self.reacao_combo)
        form.addRow("Formato do corpo:", self.formato_combo)
        form.addRow("Cor de fundo (hex):", self.fundo_edit)
        form.addRow("Cor da borda (hex):", self.borda_edit)
        form.addRow("Cor dos olhos (hex):", self.olho_edit)
        form.addRow("Cor da boca (hex):", self.boca_edit)
        form.addRow("Recadinhos iniciais (1 por linha):", self.recados_edit)
        outer.addLayout(form)
        outer.addStretch(1)

        botoes = QHBoxLayout()
        botoes.addStretch(1)
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        botoes.addWidget(cancelar)
        criar = QPushButton("Criar personagem")
        criar.setObjectName("primario")
        criar.clicked.connect(self._criar)
        botoes.addWidget(criar)
        outer.addLayout(botoes)

    def coletar_dados(self):
        """Retorna o dicionário de criação do personagem a partir dos campos."""
        recados = [ln.strip() for ln in self.recados_edit.toPlainText().splitlines() if ln.strip()]
        return {
            "id": self.id_edit.text().strip(),
            "nome": self.nome_edit.text().strip(),
            "seed": int(self.seed_spin.value()),
            "estilo_temperamento": self.temp_combo.currentData(),
            "reacao_notebook": self.reacao_combo.currentData(),
            "formato": self.formato_combo.currentData(),
            "fundo": self.fundo_edit.text().strip(),
            "borda": self.borda_edit.text().strip(),
            "olho": self.olho_edit.text().strip(),
            "boca": self.boca_edit.text().strip(),
            "recadinhos": recados,
        }

    def _criar(self):
        """Gera os arquivos do novo personagem e avisa a tela principal."""
        try:
            pet_id = config.criar_pet_personalizado(self.paths, self.coletar_dados())
        except Exception as error:
            QMessageBox.warning(self, "Erro ao criar personagem", str(error))
            return
        self.pet_criado.emit(pet_id)
        self.accept()
