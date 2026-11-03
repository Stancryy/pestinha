"""
CONQUISTAS - contadores e conquistas locais do pet, salvos em `memory/pets/<id>/achievements.json`.

Tudo é validado na leitura: dados inválidos ou arquivo corrompido são ignorados sem perder o resto.
"""

import time

from ..store import read_json, write_json

# (id, título, descrição, chave_contador, meta)
CATALOGO_CONQUISTAS = (
    ("primeiro_carinho", "Primeiro Cafuné", "Fez o primeiro carinho na Mia.", "carinhos", 1),
    ("cem_carinhos", "100 Carinhos", "Deu 100 carinhos acumulados no pet.", "carinhos", 100),
    ("sobreviveu_revolucao", "Sobreviveu à Revolução", "Enfrentou o estágio 4 de revolução.", "revolucoes", 1),
    ("foco_pomodoro", "Parceiros de Foco", "Completou um ciclo de Pomodoro junto com o pet.", "pomodoros", 1),
    ("commit_festejado", "Commit Comemorado", "Comemorou um commit local no Git.", "commits", 1),
    ("fuga_cantinho", "Mestre da Fuga", "Viu o pet escapar do cantinho do castigo.", "fugas", 1),
    ("festa_fogos", "Noite de Fogos", "Soltou fogos de artifício de pura alegria.", "fogos", 1),
)

CHAVES_CONTADOR = frozenset(c[3] for c in CATALOGO_CONQUISTAS)
IDS_CONQUISTAS = frozenset(c[0] for c in CATALOGO_CONQUISTAS)


class Conquistas:
    """Gerencia contadores de progresso e conquistas desbloqueadas de um personagem."""

    def __init__(self, path=None):
        """Inicializa contadores zerados e carrega do arquivo se fornecido."""
        self.path = path
        self.contadores = {k: 0 for k in CHAVES_CONTADOR}
        self.desbloqueadas = {}     # {id_conquista: timestamp_epoch}
        if path is not None:
            self.load(path)

    def registrar(self, chave, quantidade=1, agora=None):
        """
        Soma `quantidade` ao contador `chave` e devolve a lista de `[(id, titulo, descricao)]`
        das conquistas recém-desbloqueadas nesta chamada.
        """
        if chave not in self.contadores or isinstance(quantidade, bool) or not isinstance(quantidade, (int, float)):
            return []
        inc = max(0, int(quantidade))
        if inc <= 0:
            return []
        self.contadores[chave] = self.contadores.get(chave, 0) + inc
        ts = time.time() if agora is None else float(agora)
        novas = []
        for cid, titulo, desc, k_cont, meta in CATALOGO_CONQUISTAS:
            if k_cont == chave and cid not in self.desbloqueadas and self.contadores[chave] >= meta:
                self.desbloqueadas[cid] = ts
                novas.append((cid, titulo, desc))
        return novas

    def resumo(self):
        """Lista completa de conquistas com estado atual para o painel Diário do Pet."""
        out = []
        for cid, titulo, desc, k_cont, meta in CATALOGO_CONQUISTAS:
            atual = self.contadores.get(k_cont, 0)
            out.append({
                "id": cid,
                "titulo": titulo,
                "descricao": desc,
                "contador": k_cont,
                "atual": atual,
                "meta": meta,
                "desbloqueada": cid in self.desbloqueadas,
                "quando": self.desbloqueadas.get(cid),
            })
        return out

    def save(self, path=None):
        """Salva os contadores e conquistas em JSON."""
        alvo = path or self.path
        if alvo is None:
            return
        write_json(alvo, {
            "contadores": dict(self.contadores),
            "desbloqueadas": dict(self.desbloqueadas),
        }, indent=2)

    def load(self, path=None):
        """Carrega contadores e conquistas de JSON, descartando chaves ou tipos inválidos."""
        alvo = path or self.path
        if alvo is None:
            return False
        dados = read_json(alvo, default=None)
        if not isinstance(dados, dict):
            return False
        bruto_cont = dados.get("contadores")
        if isinstance(bruto_cont, dict):
            for k, v in bruto_cont.items():
                if k in CHAVES_CONTADOR and not isinstance(v, bool) and isinstance(v, (int, float)) and v >= 0:
                    self.contadores[k] = int(v)
        bruto_desb = dados.get("desbloqueadas")
        if isinstance(bruto_desb, dict):
            for cid, ts in bruto_desb.items():
                if cid in IDS_CONQUISTAS and not isinstance(ts, bool) and isinstance(ts, (int, float)) and ts >= 0:
                    self.desbloqueadas[cid] = float(ts)
        # Garante consistência se um contador já atingiu a meta
        for cid, _titulo, _desc, k_cont, meta in CATALOGO_CONQUISTAS:
            if self.contadores.get(k_cont, 0) >= meta and cid not in self.desbloqueadas:
                self.desbloqueadas[cid] = time.time()
        return True
