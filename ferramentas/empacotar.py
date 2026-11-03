"""Gera o ícone `.ico` da Mia, os metadados de versão e empacota o executável `--onedir` em `executáveis/Pestinha/`."""

from pathlib import Path
import shutil
import struct
import subprocess
import sys

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage

ROOT = Path(__file__).resolve().parent.parent
ICONE_DEST = ROOT / "assets" / "comum" / "icone_mia.ico"
SPRITE_ORIGEM = ROOT / "pets" / "mia" / "sprites" / "feliz.webp"

VERSION_INFO_TEMPLATE = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(0, 8, 0, 0),
    prodvers=(0, 8, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '041604B0',
        [StringStruct('CompanyName', 'Pestinha — Versão Personalizada'),
        StringStruct('FileDescription', 'Pestinha (Mia) — Pet virtual com rede neural pulsada'),
        StringStruct('FileVersion', '0.8.0.0'),
        StringStruct('InternalName', 'Pestinha'),
        StringStruct('LegalCopyright', 'GPL-3.0-or-later'),
        StringStruct('OriginalFilename', 'Pestinha.exe'),
        StringStruct('ProductName', 'Pestinha'),
        StringStruct('ProductVersion', '0.8.0')])
      ]),
    VarFileInfo([VarStruct('Translation', [1046, 1200])])
  ]
)
"""


def gerar_icone(origem=SPRITE_ORIGEM, destino=ICONE_DEST):
    """Converte o sprite `feliz.webp` da Mia em um arquivo `.ico` multi-resolução (16 a 256 px) usando Qt."""
    QGuiApplication.instance() or QGuiApplication([])
    destino.parent.mkdir(parents=True, exist_ok=True)
    base = QImage(str(origem))
    tamanhos = [16, 32, 48, 64, 128, 256]
    blocos = []
    for lado in tamanhos:
        esc = base.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        arr = QByteArray()
        buf = QBuffer(arr)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        esc.save(buf, "PNG")
        buf.close()
        blocos.append((lado, bytes(arr)))

    cabecalho = struct.pack("<HHH", 0, 1, len(blocos))
    offset = 6 + 16 * len(blocos)
    entradas = []
    for lado, dados in blocos:
        dim = 0 if lado >= 256 else lado
        entradas.append(struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(dados), offset))
        offset += len(dados)

    destino.write_bytes(cabecalho + b"".join(entradas) + b"".join(d for _, d in blocos))
    return destino


def empacotar_onedir():
    """Compila `Pestinha.exe` no modo `--onedir` com ícone e metadados de versão e copia `assets/` e `pets/`."""
    icone = gerar_icone()
    pasta_build = ROOT / "executáveis" / "_build_tmp"
    pasta_dist = ROOT / "executáveis"
    pasta_app = pasta_dist / "Pestinha"
    pasta_build.mkdir(parents=True, exist_ok=True)
    arq_versao = pasta_build / "version_info.txt"
    arq_versao.write_text(VERSION_INFO_TEMPLATE, encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--noconsole",
        "--name",
        "Pestinha",
        "--distpath",
        str(pasta_dist),
        "--workpath",
        str(pasta_build / "work"),
        "--specpath",
        str(pasta_build),
        "--icon",
        str(icone),
        "--version-file",
        str(arq_versao),
        str(ROOT / "main.py"),
    ]
    subprocess.run(cmd, cwd=str(ROOT), check=True)

    for nome_pasta in ("assets", "pets"):
        destino_sub = pasta_app / nome_pasta
        if destino_sub.exists():
            shutil.rmtree(destino_sub)
        shutil.copytree(ROOT / nome_pasta, destino_sub)

    shutil.rmtree(pasta_build, ignore_errors=True)
    return pasta_app / "Pestinha.exe"


if __name__ == "__main__":
    exe = empacotar_onedir()
    print(f"Build concluído com sucesso: {exe}")
