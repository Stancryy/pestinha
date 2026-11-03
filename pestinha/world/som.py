"""
SOM - efeitos sonoros retrô 8-bit sintetizados em memória (sem arquivos externos),
opcionais e com controle de volume próprio (0..100%).
"""

import io
import math
import os
import struct
import sys
import threading
import wave

# Sequências de notas (frequência Hz, duração s) por evento
SONS_RETRO = {
    "pulo": [(380.0, 0.04), (540.0, 0.05)],
    "carinho": [(523.25, 0.05), (659.25, 0.06)],
    "fogo": [(440.0, 0.04), (660.0, 0.04), (880.0, 0.07)],
    "conquista": [(523.25, 0.05), (659.25, 0.05), (783.99, 0.05), (1046.5, 0.09)],
    "protesto": [(220.0, 0.06), (185.0, 0.08)],
}


def gerar_wav_retro(evento, volume=40, taxa=22050):
    """Gera bytes WAV PCM 16-bit em memória para `evento` com `volume` de 0 a 100."""
    notas = SONS_RETRO.get(evento, SONS_RETRO["pulo"])
    vol = max(0.0, min(100.0, float(volume))) / 100.0
    amostras = bytearray()
    for freq, dur in notas:
        n = max(1, int(taxa * dur))
        for i in range(n):
            env = 1.0 - (i / n) * 0.6
            val = math.sin(2.0 * math.pi * freq * (i / taxa))
            pcm = int(max(-32767, min(32767, val * env * vol * 14000)))
            amostras.extend(struct.pack("<h", pcm))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes(bytes(amostras))
    return buf.getvalue()


class SoundFX:
    """Reprodutor leve de efeitos sonoros opcionais com controle de volume."""

    def __init__(self):
        """Guarda o último som tocado (para inspeção e testes)."""
        self.ultimo_som = None

    def tocar(self, evento, ativo=False, volume=40, nao_perturbe=False):
        """Sintetiza e toca o efeito se `ativo=True`, `volume > 0` e fora de `nao_perturbe`."""
        if not ativo or nao_perturbe or volume <= 0:
            return False
        wav_bytes = gerar_wav_retro(evento, volume=volume)
        self.ultimo_som = (evento, int(volume), len(wav_bytes))
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            return True
        if sys.platform == "win32":
            # O winsound não toca da memória em modo assíncrono (RuntimeError): toca síncrono numa thread.
            def _tocar():
                try:
                    import winsound
                    winsound.PlaySound(wav_bytes, winsound.SND_MEMORY | winsound.SND_NODEFAULT)
                except Exception:
                    pass
            threading.Thread(target=_tocar, daemon=True).start()
        return True

