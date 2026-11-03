"""Testes de rotação de log por tamanho e relatório local de travamento (crash report)."""

from pathlib import Path

from pestinha import log as log_module
from pestinha.paths import Paths


def test_paths_tem_crash_log(tmp_path):
    p = Paths(root=tmp_path)
    assert p.crash_log == tmp_path / "memory" / "logs" / "crash.log"


def test_log_rotaciona_quando_passa_do_limite(tmp_path, monkeypatch):
    monkeypatch.setattr(log_module, "MAX_BYTES", 200)
    arq = tmp_path / "logs" / "pestinha.log"
    log_module.setup(arq)
    for i in range(15):
        log_module.log(f"linha de teste número {i:02d} com texto extra")
    assert arq.exists()
    backup1 = Path(f"{arq}.1")
    assert backup1.exists()
    assert "linha de teste" in backup1.read_text(encoding="utf-8")
    assert "linha de teste" in arq.read_text(encoding="utf-8")
    log_module.desligar_arquivo()


def test_crash_report_grava_excecao_localmente(tmp_path):
    p = Paths(root=tmp_path)
    log_module.setup(p.log, p.crash_log)
    try:
        raise RuntimeError("falha simulada no teste")
    except RuntimeError as exc:
        log_module.registrar_crash(type(exc), exc, exc.__traceback__)
    assert p.crash_log.exists()
    texto = p.crash_log.read_text(encoding="utf-8")
    assert "CRASH" in texto
    assert "RuntimeError: falha simulada no teste" in texto
    log_module.desligar_arquivo()


def test_desligar_arquivo_impede_recriar_crash_log(tmp_path):
    p = Paths(root=tmp_path)
    log_module.setup(p.log, p.crash_log)
    log_module.desligar_arquivo()
    try:
        raise ValueError("não deve gravar")
    except ValueError as exc:
        log_module.registrar_crash(type(exc), exc, exc.__traceback__)
    assert not p.crash_log.exists()

