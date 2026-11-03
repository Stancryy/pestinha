"""
SEGUNDO PET - suporte opcional a um 2º personagem na tela ao mesmo tempo,
interagindo com o pet principal (brincam juntos ou brigam/trombam).
"""

import math
import random

from .. import config
from ..body.desenho_rosto import aparencia_de
from ..body.pet import PetWindow
from ..body.pet_state import PetState

DISTANCIA_INTERACAO = 125.0
COOLDOWN_INTERACAO_S = 3.5


class SegundoPetController:
    """Controla a janela, a física e as interações sociais de um 2º pet opcional na tela."""

    def __init__(self, paths, pet_principal_id):
        """Prepara o controlador sem criar janela até ser ativado."""
        self.paths = paths
        self.pet_principal_id = pet_principal_id
        self.pet_id = None
        self.nome = None
        self.estado = None
        self.janela = None
        self.alvo_x = None
        self.proximo_passo = 0.0
        self.ultima_interacao = -1e9
        self.ultima_acao_social = None   # "brincar" ou "brigar"

    def escolher_segundo_id(self, preferido=""):
        """Escolhe outro `<pet>.json` disponível além do principal, ou None se só houver um."""
        todos = config.list_pets(self.paths)
        if preferido and preferido in todos and preferido != self.pet_principal_id:
            return preferido
        outros = [p for p in todos if p != self.pet_principal_id]
        return outros[0] if outros else None

    def sincronizar(self, ativo, visivel, bounds, preferido=""):
        """Cria, mostra ou esconde o 2º pet conforme a permissão e os personagens instalados."""
        escolhido = self.escolher_segundo_id(preferido) if ativo else None
        if not ativo or not escolhido:
            if self.janela is not None:
                self.janela.setVisible(False)
            return False
        if self.janela is None or self.pet_id != escolhido:
            if self.janela is not None:
                self.janela.close()
            self.pet_id = escolhido
            pet_def = config.load_pet(self.paths, escolhido)
            self.nome = pet_def["nome"]
            self.estado = PetState()
            left, top, _right, _bottom = bounds
            self.janela = PetWindow(left + 240, top + 120, self.estado)
            self.janela.aparencia = aparencia_de(pet_def.get("aparencia"))
        self.janela.setVisible(bool(visivel))
        return bool(visivel)

    def tick(self, dt, now, bounds, areas, monitores, platforms, pet_principal, estado_principal, drives_principal, ball=None):
        """Atualiza física, passeio e interação (brincar ou brigar) entre os dois pets."""
        if self.janela is None or not self.janela.isVisible():
            return None
        body2 = self.janela.body
        body1 = pet_principal.body
        body2.step(dt, bounds, platforms, areas, monitores)

        # Passeio simples ou ir atrás da bolinha
        left, _top, right, _bottom = bounds
        if body2.grounded and not body2.held and now >= self.proximo_passo:
            self.proximo_passo = now + random.uniform(2.0, 4.5)
            if ball is not None and ball.isVisible() and random.random() < 0.6:
                self.alvo_x = max(left + 80, min(right - 80, ball.body.x))
            else:
                self.alvo_x = random.uniform(left + 90, right - 90)
        if self.alvo_x is not None and body2.grounded and not body2.held:
            if abs(body2.x - self.alvo_x) < 15:
                self.alvo_x = None
                body2.vx = 0.0
            else:
                body2.vx = (1 if self.alvo_x > body2.x else -1) * 145.0

        # Interação entre os dois pets quando se encontram
        acao = None
        dist = math.hypot(body1.x - body2.x, body1.y - body2.y)
        if dist < DISTANCIA_INTERACAO and now - self.ultima_interacao >= COOLDOWN_INTERACAO_S:
            self.ultima_interacao = now
            direcao = 1 if body2.x >= body1.x else -1
            if estado_principal.protest_stage >= 2 or estado_principal.emotion == "bravo":
                # Brigam / trombam: cada um pula para um lado com cara de bravo
                acao = "brigar"
                self.estado.emotion = "bravo"
                if body2.grounded:
                    body2.jump(direcao * 220.0, -320.0, direcao * 180.0)
                if body1.grounded and not body1.held:
                    body1.jump(-direcao * 180.0, -260.0, -direcao * 140.0)
            else:
                # Brincam juntos: pulinho alegre e reduz carência/tédio do pet principal
                acao = "brincar"
                self.estado.emotion = "feliz"
                if body2.grounded:
                    body2.jump(-direcao * 90.0, -260.0)
                drives_principal.stimulate("novelty", 0.15)
                drives_principal.touched("poke", 0.2)
                if ball is not None and ball.isVisible() and math.hypot(ball.body.x - body2.x, ball.body.y - body2.y) < 180:
                    ball.body.vx = -direcao * 340.0
                    ball.body.vy = -280.0
                    ball.body.grounded = False
            self.ultima_acao_social = acao

        self.janela.animate(now)
        return acao

    def fechar(self):
        """Fecha a janela do 2º pet ao encerrar o programa."""
        if self.janela is not None:
            self.janela.close()
            self.janela = None

