"""
LOG - um lugar só para mensagens do app: terminal, arquivo rotativo e crash report em memory/logs/.

O arquivo de log é rotacionado quando passa de 1 MB (mantém até 3 backups .1, .2, .3 e preserva
as linhas mais recentes no arquivo ativo). Se o arquivo não puder ser escrito, a mensagem vai só
para o terminal. Também registra relatórios locais de travamento (crash.log) sem dados sensíveis.
"""

import datetime
import os
import platform
import sys
import traceback
from pathlib import Path

MAX_BYTES = 1_000_000
MAX_BACKUPS = 3
_file = None
_crash_file = None
_hook_instalado = False


def setup(path, crash_path=None):
    """Escolhe o arquivo do log e o de crash report (criados sob demanda)."""
    global _file, _crash_file
    _file = Path(path)
    _crash_file = Path(crash_path) if crash_path is not None else _file.parent / "crash.log"


def desligar_arquivo():
    """Para de gravar em arquivo (usado ao apagar os dados: nada pode recriar a pasta)."""
    global _file, _crash_file
    _file = None
    _crash_file = None


def _rotacionar_backups(caminho):
    """Desloca os backups (.2 -> .3, .1 -> .2) para abrir espaço para o .1."""
    for idx in range(MAX_BACKUPS - 1, 0, -1):
        origem = Path(f"{caminho}.{idx}")
        destino = Path(f"{caminho}.{idx + 1}")
        if origem.exists():
            try:
                origem.replace(destino)
            except OSError:
                pass


def _trim():
    """Rotaciona o log para .1 quando passa do limite e mantém a metade mais recente ativa."""
    try:
        if _file is not None and _file.exists() and _file.stat().st_size > MAX_BYTES:
            _rotacionar_backups(_file)
            lines = _file.read_text(encoding="utf-8", errors="replace").splitlines()
            meio = max(1, len(lines) // 2)
            antigas = "\n".join(lines[:meio]) + "\n"
            recentes = "\n".join(lines[meio:]) + "\n"
            Path(f"{_file}.1").write_text(antigas, encoding="utf-8")
            _file.write_text(recentes, encoding="utf-8")
    except OSError:
        pass


def log(*parts):
    """Escreve uma mensagem no terminal e no arquivo do log (uma linha por chamada)."""
    text = " ".join(str(p) for p in parts)
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))
    if _file is None:
        return
    try:
        _file.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().isoformat(timespec="seconds")
        with open(_file, "a", encoding="utf-8") as f:
            f.write(f"{stamp} {text}{os.linesep}")
        _trim()
    except OSError:
        pass


def registrar_crash(exc_type, exc_value, exc_tb):
    """Grava um relatório local de travamento em crash.log (sem dados de janelas)."""
    if _crash_file is None:
        return
    try:
        _crash_file.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().isoformat(timespec="seconds")
        cabecalho = (
            f"=== CRASH {stamp} | Python {platform.python_version()} | {platform.system()} ===\n"
        )
        tb_texto = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        bloco = cabecalho + tb_texto + "\n"
        with open(_crash_file, "a", encoding="utf-8") as f:
            f.write(bloco)
        if _crash_file.stat().st_size > MAX_BYTES:
            _rotacionar_backups(_crash_file)
            conteudo = _crash_file.read_text(encoding="utf-8", errors="replace")
            Path(f"{_crash_file}.1").write_text(conteudo[: len(conteudo) // 2], encoding="utf-8")
            _crash_file.write_text(conteudo[len(conteudo) // 2 :], encoding="utf-8")
    except OSError:
        pass


def instalar_crash_handler():
    """Instala sys.excepthook para registrar exceções não tratadas no crash.log local."""
    global _hook_instalado
    if _hook_instalado:
        return

    def _excepthook(exc_type, exc_value, exc_tb):
        if not issubclass(exc_type, KeyboardInterrupt):
            registrar_crash(exc_type, exc_value, exc_tb)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook
    _hook_instalado = True
