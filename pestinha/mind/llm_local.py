"""
LLM LOCAL - geração opcional e 100% offline de recadinhos via servidor local
(Ollama em `127.0.0.1:11434` ou LM Studio / OpenAI local em `127.0.0.1:1234`),
com fallback imediato para os arquivos `.txt` do personagem.

Regra estrita de privacidade:
- Rejeita qualquer URL cujo host não seja `127.0.0.1`, `localhost` ou `::1`.
- Roda em thread separada para nunca travar a animação do pet.
"""

from collections import deque
import json
import threading
import urllib.parse
import urllib.request

HOSTS_LOCAIS = frozenset({"127.0.0.1", "localhost", "::1"})


def eh_url_local_segura(url):
    """Garante que o endpoint aponta exclusivamente para a própria máquina (loopback)."""
    if not isinstance(url, str) or not url.strip():
        return False
    try:
        parsed = urllib.parse.urlparse(url.strip())
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    return host in HOSTS_LOCAIS


def limpar_frase_llm(texto, max_chars=90):
    """Higieniza a frase gerada pelo modelo: uma linha só, sem aspas externas e curta."""
    if not isinstance(texto, str):
        return None
    linha = texto.strip().splitlines()[0].strip() if texto.strip() else ""
    linha = linha.strip("\"'“”‘’* ")
    if not linha or len(linha) < 3:
        return None
    if len(linha) > max_chars:
        linha = linha[: max_chars - 1].rstrip() + "…"
    return linha


def consultar_llm_local(endpoint, modelo, nome_pet, emocao, atividade, timeout=1.5):
    """
    Faz uma requisição HTTP local (Ollama `/api/generate` ou OpenAI `/v1/chat/completions`)
    e devolve uma frase curta, ou None se o servidor local estiver desligado.
    """
    if not eh_url_local_segura(endpoint):
        return None
    base = endpoint.strip().rstrip("/")
    prompt = (
        f"Você é {nome_pet}, uma pet virtual fofa e sarcástica de desktop. "
        f"Seu humor agora é '{emocao}' e o usuário está na atividade '{atividade}'. "
        "Escreva APENAS UMA frase curta de post-it (máximo 75 caracteres, em português, sem aspas):"
    )
    try:
        if base.endswith("/v1") or ":1234" in base:
            url = f"{base}/chat/completions" if base.endswith("/v1") else f"{base}/v1/chat/completions"
            payload = {
                "model": modelo or "local-model",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 35,
                "temperature": 0.8,
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
                bruto = dados["choices"][0]["message"]["content"]
                return limpar_frase_llm(bruto)
        else:
            url = f"{base}/api/generate"
            payload = {
                "model": modelo or "llama3.2",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 35, "temperature": 0.8},
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
                return limpar_frase_llm(dados.get("response"))
    except Exception:
        return None


class GeradorLLMLocal:
    """Fila assíncrona de frases geradas por LLM local com fallback instantâneo para `.txt`."""

    def __init__(self, consultar_fn=consultar_llm_local):
        """Inicializa o buffer local e a função de consulta (injetável nos testes)."""
        self.consultar_fn = consultar_fn
        self.fila = deque(maxlen=5)
        self._ocupado = False

    def escolher_frase(self, notes_fallback, ativo=False, endpoint="", modelo="",
                       nome_pet="Mia", emocao="observando", atividade="IDLE", sincrono=False):
        """
        Retorna uma frase do LLM local (se `ativo=True` e disponível) ou faz fallback imediato
        para `notes_fallback.pick()`.
        """
        if not ativo or not eh_url_local_segura(endpoint):
            return notes_fallback.pick() if notes_fallback else None
        if sincrono:
            frase = self.consultar_fn(endpoint, modelo, nome_pet, emocao, atividade)
            if frase:
                return frase
            return notes_fallback.pick() if notes_fallback else None
        if self.fila:
            frase = self.fila.popleft()
            self._disparar_preenchimento(endpoint, modelo, nome_pet, emocao, atividade)
            return frase
        self._disparar_preenchimento(endpoint, modelo, nome_pet, emocao, atividade)
        return notes_fallback.pick() if notes_fallback else None

    def _disparar_preenchimento(self, endpoint, modelo, nome_pet, emocao, atividade):
        """Pede uma frase em background para a próxima travessura sem bloquear o Qt."""
        if self._ocupado or len(self.fila) >= 3:
            return
        self._ocupado = True

        def tarefa():
            try:
                frase = self.consultar_fn(endpoint, modelo, nome_pet, emocao, atividade)
                if frase:
                    self.fila.append(frase)
            finally:
                self._ocupado = False

        threading.Thread(target=tarefa, daemon=True).start()

