"""Partes que os três sistemas compartilham: rodar comandos do sistema, atalhos, trava de instância e inicialização."""

import os
from pathlib import Path
import subprocess
import sys
import threading
import time

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


def uso_hardware():
    """Retorna `(cpu_percent, ram_percent)` atuais sem bloquear a thread."""
    try:
        cpu = float(psutil.cpu_percent(interval=None))
        ram = float(psutil.virtual_memory().percent)
        return max(0.0, min(100.0, cpu)), max(0.0, min(100.0, ram))
    except Exception:
        return 0.0, 0.0


def midia_tocando(apps_musica=()):
    """
    Diz se há aplicativo de música/mídia ativo (apenas booleano tocando/pausado, nunca lê títulos).
    Verifica se algum processo da categoria MUSIC está aberto em execução ativa.
    """
    nomes_alvo = {str(a).lower().removesuffix(".exe") for a in (apps_musica or ())}
    if not nomes_alvo:
        nomes_alvo = {"spotify", "musicbee", "aimp", "foobar2000", "vlc", "wmplayer", "itunes"}
    try:
        for proc in psutil.process_iter(["name"]):
            nome = (proc.info.get("name") or "").lower().removesuffix(".exe")
            if nome in nomes_alvo:
                return True
    except Exception:
        pass
    return False


def bateria_status():
    """
    Retorna `(porcentagem, conectado_na_tomada)`.
    Se o computador for um desktop ou o sensor não estiver disponível, retorna `(None, None)`.
    """
    try:
        bateria = psutil.sensors_battery()
        if bateria is None:
            return None, None
        return float(bateria.percent), bool(bateria.power_plugged)
    except Exception:
        return None, None


class MonitorDigitacao:
    """
    Monitor de velocidade de digitação (teclas por segundo).
    CONFORMIDADE COM A PRIVACIDADE:
    Conta exclusivamente a QUANTIDADE de eventos de toque por segundo,
    descartando de imediato qualquer informação sobre QUAL tecla foi pressionada.
    Nenhuma tecla, caractere, texto ou identificador de tecla é armazenado ou transmitido.
    """

    def __init__(self):
        self._contador = 0
        self._lock = threading.Lock()
        self._ultimo_calculo = time.monotonic()
        self._taxa_atual = 0.0
        self._listener = None
        self._ativo = False

    def iniciar(self):
        """Inicia o listener em segundo plano. Degrada graciosamente se indisponível."""
        if self._ativo:
            return True
        try:
            from pynput import keyboard

            def _on_press(_key):
                # Descarte imediato do argumento _key: apenas incrementa contador
                with self._lock:
                    self._contador += 1

            self._listener = keyboard.Listener(on_press=_on_press)
            self._listener.daemon = True
            self._listener.start()
            self._ativo = True
            return True
        except Exception as error:
            log(f"[teclado] monitor de digitação desligado ou indisponível: {error}")
            return False

    def parar(self):
        """Interrompe o monitor de digitação."""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        self._ativo = False

    def teclas_por_segundo(self):
        """Retorna a taxa recente de teclas/segundo (sempre >= 0.0)."""
        agora = time.monotonic()
        dt = agora - self._ultimo_calculo
        if dt >= 0.2:
            with self._lock:
                self._taxa_atual = self._contador / dt
                self._contador = 0
            self._ultimo_calculo = agora
        return self._taxa_atual


_MONITOR_DIGITACAO = None


def obter_monitor_digitacao():
    """Retorna a instância compartilhada do MonitorDigitacao."""
    global _MONITOR_DIGITACAO
    if _MONITOR_DIGITACAO is None:
        _MONITOR_DIGITACAO = MonitorDigitacao()
    return _MONITOR_DIGITACAO

