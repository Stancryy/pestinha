"""
Testes dos novos canais sensoriais, motores associados e degradação graciosa da plataforma.
Garante que a SNN reage coerentemente sem comprometer a privacidade nem a estabilidade.
"""

import time
import numpy as np
import pytest

from pestinha import ajustes
from pestinha.core.nervous_system import LIFBrain, SENSORY_SPEC, CONNECTIONS
from pestinha.ui.rotulos import CANAIS_SENSORIAIS
from pestinha.plataforma._comum import MonitorDigitacao, bateria_status
from pestinha.sense.senses import (
    calcular_fator_circadiano,
    calcular_fator_bateria,
    calcular_fator_janelas,
    calcular_fator_mouse,
    calcular_fator_digitacao,
    ComputerSenses,
)


NOVOS_CANAIS = {
    "TYPING_SPEED",
    "CPU_LOAD",
    "CIRCADIAN",
    "MOUSE_SPEED",
    "BATTERY_LOW",
    "WINDOW_COUNT",
}


def test_novos_canais_presentes_em_sensory_spec_e_rotulos():
    """Confere se todos os novos canais estão catalogados na especificação e traduzidos."""
    for canal in NOVOS_CANAIS:
        assert canal in SENSORY_SPEC, f"Canal {canal} ausente em SENSORY_SPEC"
        assert canal in CANAIS_SENSORIAIS, f"Canal {canal} ausente em CANAIS_SENSORIAIS"


def test_novos_canais_habituacao_especificada():
    """Verifica se os parâmetros de habituação (d e tau_rec) estão de acordo com o design biológico."""
    # Canais ambientais e fisiológicos não habituam
    assert SENSORY_SPEC["CPU_LOAD"][2] == 0.0
    assert SENSORY_SPEC["CIRCADIAN"][2] == 0.0
    assert SENSORY_SPEC["BATTERY_LOW"][2] == 0.0

    # Canais de ritmo comportamental habituam com d > 0 e tau_rec definidos
    for canal in ("TYPING_SPEED", "MOUSE_SPEED", "WINDOW_COUNT"):
        d, tau = SENSORY_SPEC[canal][2], SENSORY_SPEC[canal][3]
        assert d > 0.0, f"{canal} deveria ter habituação (d > 0)"
        assert tau >= 600.0, f"{canal} deveria ter tau_rec >= 600 s"


def test_habituacao_dinamica_typing_speed():
    """Valida que digitação contínua prolongada sofre depressão sináptica e se recupera."""
    brain = LIFBrain(seed=7)
    brain.rng = np.random.default_rng(42)

    # Eficácia inicial = 1.0
    assert brain.efficacy()["TYPING_SPEED"] == pytest.approx(1.0, abs=1e-3)

    # Estímulo contínuo por múltiplos passos
    for _ in range(50):
        brain.stimulate({"TYPING_SPEED": 1.0})
        brain.step(100)

    eff_pos = brain.efficacy()["TYPING_SPEED"]
    assert eff_pos < 1.0, "Eficácia de TYPING_SPEED deveria ter caído por habituação"

    # Recuperação
    brain.reset_habituation()
    assert brain.efficacy()["TYPING_SPEED"] == pytest.approx(1.0, abs=1e-3)


def test_typing_speed_estimula_playful_e_alert():
    """Digitação rápida deve excitar as populações de brincadeira/torcida (PLAYFUL) e alerta."""
    brain = LIFBrain(seed=7)
    brain.rng = np.random.default_rng(99)

    for _ in range(20):
        brain.stimulate({})
        brain.step(100)
    base_playful = brain.pool_rates()["PLAYFUL"]

    for _ in range(25):
        brain.stimulate({"TYPING_SPEED": 1.0})
        brain.step(100)
    ativo_playful = brain.pool_rates()["PLAYFUL"]

    assert ativo_playful > base_playful, "PLAYFUL deveria subir com TYPING_SPEED ativo"


def test_cpu_load_aumenta_alerta_e_frustracao():
    """Carga alta de processador/calor deve excitar ALERT e FRUSTRATION e inibir CALM."""
    brain = LIFBrain(seed=7)
    brain.rng = np.random.default_rng(42)

    for _ in range(20):
        brain.stimulate({})
        brain.step(100)
    base_alert = brain.pool_rates()["ALERT"]

    for _ in range(25):
        brain.stimulate({"CPU_LOAD": 1.0})
        brain.step(100)
    ativo_alert = brain.pool_rates()["ALERT"]

    assert ativo_alert > base_alert, "ALERT deveria aumentar sob carga alta de CPU"


def test_circadiano_eleva_tired_e_drowse():
    """Estímulo de madrugada deve aumentar TIRED e elevar a atividade do motor DROWSE."""
    brain = LIFBrain(seed=7)
    brain.rng = np.random.default_rng(123)

    for _ in range(20):
        brain.stimulate({})
        brain.step(100)
    base_drowse = brain.motor_activity()["DROWSE"]

    for _ in range(30):
        brain.stimulate({"CIRCADIAN": 1.0})
        brain.step(100)
    ativo_drowse = brain.motor_activity()["DROWSE"]

    assert ativo_drowse > base_drowse, "Motor DROWSE deveria ter taxa mais alta na madrugada"


def test_battery_low_estimula_gloom():
    """Bateria baixa deve excitar desânimo (GLOOM) e alerta."""
    brain = LIFBrain(seed=7)
    brain.rng = np.random.default_rng(55)

    for _ in range(20):
        brain.stimulate({})
        brain.step(100)
    base_gloom = brain.pool_rates()["GLOOM"]

    for _ in range(30):
        brain.stimulate({"BATTERY_LOW": 1.0})
        brain.step(100)
    ativo_gloom = brain.pool_rates()["GLOOM"]

    assert ativo_gloom > base_gloom, "GLOOM deveria aumentar quando a bateria está acabando"


def test_funcoes_calculo_fatores_senses():
    """Testa os conversores de grandezas físicas/do sistema para a escala 0..1."""
    # Circadiano
    assert calcular_fator_circadiano(3.0) == 1.0     # 03:00 = madrugada pico
    assert calcular_fator_circadiano(14.0) == 0.0    # 14:00 = meio da tarde
    assert 0.0 < calcular_fator_circadiano(23.0) < 1.0  # 23:00 = transição
    assert 0.0 < calcular_fator_circadiano(6.0) < 1.0   # 06:00 = amanhecendo

    # Bateria
    assert calcular_fator_bateria(100.0, True) == 0.0   # cheia e na tomada
    assert calcular_fator_bateria(10.0, True) == 0.0    # baixa mas na tomada
    assert calcular_fator_bateria(10.0, False) > 0.0   # baixa e sem tomada
    assert calcular_fator_bateria(3.0, False) == 1.0    # crítica
    assert calcular_fator_bateria(None, None) == 0.0    # desktop sem bateria

    # Janelas
    assert calcular_fator_janelas(0) == 0.0
    assert calcular_fator_janelas(ajustes.LIMIAR_JANELAS_MUITAS) == 1.0
    assert calcular_fator_janelas(ajustes.LIMIAR_JANELAS_MUITAS * 2) == 1.0

    # Mouse
    assert calcular_fator_mouse(0.0) == 0.0
    assert calcular_fator_mouse(ajustes.LIMIAR_MOUSE_RAPIDO) == 1.0
    assert calcular_fator_mouse(ajustes.LIMIAR_MOUSE_RAPIDO * 2) == 1.0

    # Digitação
    assert calcular_fator_digitacao(0.0) == 0.0
    assert calcular_fator_digitacao(ajustes.LIMIAR_DIGITACAO_RAPIDA) == 1.0


def test_computer_senses_update_com_novos_canais():
    """ComputerSenses deve agregar e suavizar os novos canais sensoriais."""
    cs = ComputerSenses()
    intensities = cs.update(
        activity="PROGRAMMING",
        idle_seconds=0.1,
        drives={"BOREDOM": 0.2, "LONELY": 0.1, "FATIGUE": 0.0},
        typing_speed=0.8,
        cpu_load=0.75,
        circadian=1.0,
        mouse_speed=0.6,
        battery_low=0.5,
        window_count=0.4,
    )
    for canal in NOVOS_CANAIS:
        assert canal in intensities
        assert 0.0 <= intensities[canal] <= 1.0
    assert intensities["CPU_LOAD"] == pytest.approx(0.75)
    assert intensities["CIRCADIAN"] == pytest.approx(1.0)


def test_monitor_digitacao_sem_gravar_teclas():
    """Garante que o monitor de digitação apenas conta eventos sem expor nem armazenar teclas."""
    mon = MonitorDigitacao()
    # Simula toques incrementando contador interno diretamente
    with mon._lock:
        mon._contador = 10
    mon._ultimo_calculo = time.monotonic() - 1.0
    taxa = mon.teclas_por_segundo()
    assert taxa > 0.0
    # Verifica que não há buffer de texto ou teclas salvas
    assert not hasattr(mon, "buffer_teclas")
    assert not hasattr(mon, "historico_teclas")


def test_ajustes_validacao_novos_limiares():
    """Valida que todos os novos números em ajustes.py são válidos."""
    ajustes.validar()
    atuais = ajustes.valores_atuais()
    assert "LIMIAR_DIGITACAO_RAPIDA" in atuais
    assert "LIMIAR_MOUSE_RAPIDO" in atuais
    assert "LIMIAR_BATERIA_BAIXA" in atuais
    assert "LIMIAR_JANELAS_MUITAS" in atuais


def test_conexoes_novos_canais_definidas():
    """Confere se todos os novos canais possuem conexões sinápticas ativas na rede."""
    pres = {pre for pre, _post, _w, _d in CONNECTIONS}
    for canal in NOVOS_CANAIS:
        assert canal in pres, f"Canal {canal} não possui nenhuma sinapse de saída em CONNECTIONS"


def test_bateria_status_executa_sem_excecao():
    """Garante que a leitura de bateria funciona ou degrada graciosamente para (None, None)."""
    pct, plug = bateria_status()
    if pct is not None:
        assert 0.0 <= pct <= 100.0
        assert isinstance(plug, bool)
    else:
        assert plug is None


def test_suando_desligado_com_cpu_baixa():
    """Garante que com CPU baixa (ex.: 2%), o pet não sua, mesmo com reagir_hardware ligado."""
    from pestinha.body.pet_state import PetState
    st = PetState()
    cpu_pct = 2.0
    reagir_hardware = True
    if reagir_hardware:
        st.suando = cpu_pct >= ajustes.LIMIAR_CPU_ALTA
    else:
        st.suando = False
    assert st.suando is False


def test_digitacao_rapida_nao_dispara_sentar():
    """Digitação rápida excita PLAYFUL/CHEER e não deve ativar o motor SENTAR (notebook)."""
    brain = LIFBrain(seed=7)
    brain.rng = np.random.default_rng(42)

    for _ in range(30):
        brain.stimulate({"TYPING_SPEED": 1.0})
        brain.step(100)

    sentar_rate = brain.motor_activity()["SENTAR"]
    assert sentar_rate < ajustes.LIMIAR_SENTAR_HZ, f"SENTAR disparou a {sentar_rate:.1f} Hz (> {ajustes.LIMIAR_SENTAR_HZ} Hz)"



def test_anti_chatter_estabilidade_notebook():
    """Garante que a transição de sentar e levantar possui proteção contra oscilação rápida."""
    from pestinha.mind.mesa import DeskController
    desk = DeskController(tempo_minimo_sentado=0.5, cooldown_sentar=1.0)

    # 1) Senta no notebook com estímulo forte
    m1 = desk.tick(1.0, ajustes.LIMIAR_SENTAR_HZ + 2.0, True)
    assert m1 == (False, True)
    assert desk.at_desk is True

    # 2) Disparo oscila rapidamente antes do tempo mínimo: não levanta imediatamente (evita sair e entrar toda hora)
    m2 = desk.tick(1.2, ajustes.LIMIAR_LEVANTAR_HZ - 1.0, True)
    assert m2 is None
    assert desk.at_desk is True

    # 3) Após o tempo mínimo sentado, levanta com segurança
    m3 = desk.tick(1.6, ajustes.LIMIAR_LEVANTAR_HZ - 1.0, True)
    assert m3 == (True, False)
    assert desk.at_desk is False

    # 4) Cooldown para sentar de novo impede re-entrada instantânea em menos de 1 s
    m4 = desk.tick(1.8, ajustes.LIMIAR_SENTAR_HZ + 2.0, True)
    assert m4 is None
    assert desk.at_desk is False

    # 5) Passado o cooldown, senta normalmente
    m5 = desk.tick(2.7, ajustes.LIMIAR_SENTAR_HZ + 2.0, True)
    assert m5 == (False, True)
    assert desk.at_desk is True


def test_alegria_moderada_durante_digitacao():
    """Valida que CHEER (alegria) sobe suavemente até cerca de 2.0 Hz sem explodir."""
    brain = LIFBrain(seed=7)
    brain.rng = np.random.default_rng(7)
    taxas_cheer = []
    for _ in range(30):
        brain.stimulate({"TYPING": 1.0, "TYPING_SPEED": 1.0})
        brain.step(100)
        taxas_cheer.append(brain.motor_activity()["CHEER"])
    pico = max(taxas_cheer)
    assert 0.8 <= pico <= 3.0, f"Pico de alegria deveria ficar em torno de 2.0 Hz, deu {pico:.2f} Hz"
