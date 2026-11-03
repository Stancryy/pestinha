"""Partes que os três sistemas compartilham: rodar comandos do sistema, atalhos, trava de instância e inicialização."""

import os
from pathlib import Path
import subprocess
import sys

import psutil

from ..log import log
from ..paths import ROOT

MODS_PADRAO = frozenset({"CTRL", "ALT", "SHIFT"})
TECLA_PADRAO = "B"


def parse_atalho(texto):
    """Interpreta um atalho como 'Ctrl + Alt + Shift + B' e devolve (conjunto_mods, tecla)."""
    if not isinstance(texto, str) or not texto.strip():
        return set(MODS_PADRAO), TECLA_PADRAO
    partes = [p.strip().upper() for p in texto.split("+") if p.strip()]
    mods = set()
    tecla = None
    for p in partes:
        if p in ("CTRL", "CONTROL"):
            mods.add("CTRL")
        elif p in ("ALT", "OPTION"):
            mods.add("ALT")
        elif p == "SHIFT":
            mods.add("SHIFT")
        elif (len(p) == 1 and p.isalnum()) or (p.startswith("F") and p[1:].isdigit() and 1 <= int(p[1:]) <= 12):
            tecla = p
    if not mods or tecla is None:
        return set(MODS_PADRAO), TECLA_PADRAO
    return mods, tecla


def formatar_atalho(texto):
    """Normaliza o texto de um atalho para exibição ('Ctrl + Alt + Shift + B')."""
    mods, tecla = parse_atalho(texto)
    ordem = [nome for chave, nome in (("CTRL", "Ctrl"), ("ALT", "Alt"), ("SHIFT", "Shift")) if chave in mods]
    ordem.append(tecla)
    return " + ".join(ordem)


def adquirir_trava_instancia(lock_path, meu_pid=None, pid_ativo_fn=None):
    """Garante instância única gravando o PID em `lock_path`. Devolve False se já houver outra ativa."""
    caminho = Path(lock_path)
    pid_atual = os.getpid() if meu_pid is None else int(meu_pid)
    checar_pid = pid_ativo_fn or psutil.pid_exists
    if caminho.exists():
        try:
            texto = caminho.read_text(encoding="utf-8").strip()
            pid_salvo = int(texto)
            if pid_salvo != pid_atual and checar_pid(pid_salvo):
                return False
        except (OSError, ValueError):
            pass
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(str(pid_atual), encoding="utf-8")
    except OSError as error:
        log(f"[instância] não gravou lock: {error}")
    return True


def liberar_trava_instancia(lock_path, meu_pid=None):
    """Remove o arquivo de trava se pertencer ao processo atual."""
    caminho = Path(lock_path)
    if not caminho.exists():
        return
    pid_atual = os.getpid() if meu_pid is None else int(meu_pid)
    try:
        texto = caminho.read_text(encoding="utf-8").strip()
        if meu_pid is None or texto == str(pid_atual):
            caminho.unlink(missing_ok=True)
    except OSError:
        pass


def caminho_atalho_inicializar(pasta_startup=None):
    """Caminho do script de inicialização na pasta Startup do usuário."""
    if pasta_startup is not None:
        base = Path(pasta_startup)
    else:
        appdata = os.environ.get("APPDATA", "")
        base = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" if appdata else ROOT
    return base / "Pestinha.vbs"


def iniciar_com_windows_ativo(pasta_startup=None):
    """Diz se o atalho de inicialização automática está presente."""
    return caminho_atalho_inicializar(pasta_startup).exists()


def configurar_iniciar_com_windows(ativo, pasta_startup=None):
    """Cria ou remove o lançador silencioso (Pestinha.vbs) na pasta Inicializar do Windows."""
    atalho = caminho_atalho_inicializar(pasta_startup)
    if not ativo:
        try:
            atalho.unlink(missing_ok=True)
            return True
        except OSError as error:
            log(f"[inicializar] não removeu atalho: {error}")
            return False
    try:
        atalho.parent.mkdir(parents=True, exist_ok=True)
        if getattr(sys, "frozen", False):
            cmd = f'""{sys.executable}"" --direto'
            workdir = str(Path(sys.executable).resolve().parent)
        else:
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            exe = pythonw if pythonw.exists() else Path(sys.executable)
            cmd = f'""{exe}"" ""{ROOT / "main.py"}"" --direto'
            workdir = str(ROOT)
        conteudo = (
            'Set WshShell = CreateObject("WScript.Shell")\n'
            f'WshShell.CurrentDirectory = "{workdir}"\n'
            f'WshShell.Run "{cmd}", 0, False\n'
        )
        atalho.write_text(conteudo, encoding="utf-8")
        return True
    except OSError as error:
        log(f"[inicializar] não criou atalho: {error}")
        return False


def rodar(comando, tempo=1.0):
    """Saída do comando (texto) ou None se ele não existe, falhou ou demorou demais."""
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=tempo, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return resultado.stdout if resultado.returncode == 0 else None


def atalho_pynput(callback, atalho="Ctrl+Alt+Shift+B"):
    """Registra atalho global em qualquer lugar do sistema via pynput."""
    try:
        from pynput import keyboard
    except Exception:
        log("[pânico] pynput não está instalado: o atalho global fica desligado (o menu da bandeja funciona)")
        return False
    mods, tecla = parse_atalho(atalho)
    partes = [f"<{m.lower()}>" for m in ("CTRL", "ALT", "SHIFT") if m in mods]
    partes.append(tecla.lower() if len(tecla) == 1 else f"<{tecla.lower()}>")
    combo = "+".join(partes)
    try:
        listener = keyboard.GlobalHotKeys({combo: callback})
        listener.daemon = True
        listener.start()
    except Exception as error:
        log(f"[pânico] não deu para registrar o atalho: {error}")
        return False
    return True
