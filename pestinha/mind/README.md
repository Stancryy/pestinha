# `pestinha/mind/`

> Gerado por `ferramentas/gerar_readmes.py` a partir das docstrings. Não edite à mão: rode o script.

Controladores de decisão: ligam o que a rede decide à cena (sono, mesa, protesto, travessuras, festa, revolução, cantinho do castigo).

**Pode importar de:** core, sense, body, world (e dos módulos compartilhados). A regra é verificada por `tests/test_arquitetura.py`.

| Arquivo | O que faz |
|---|---|
| `castigo_ctl.py` | Uma plaquinha de cartoon que você arrasta para onde quiser. |
| `companhia.py` | Funções de companhia para quem programa: Pomodoro no notebook, lembretes gentis de água/postura e comemoração de commits locais do Git. |
| `festa.py` | O fogo de artifício do pet feliz: a alegria da rede enche a euforia. |
| `llm_local.py` | Geração opcional e 100% offline de recadinhos via servidor local (Ollama em `127.0.0.1:11434` ou LM Studio / OpenAI local em `127.0.0.1:1234`), com fallback imediato para os arquivos `.txt` do personagem. |
| `mesa.py` | O computadorzinho do pet: sentar e levantar do notebook. |
| `mischief_ctl.py` | Quando e como ele apronta, e o que a dispensa causa. |
| `protest_ctl.py` | Liga o protesto (core/protesto.py) à cena: cartaz, estágio, repressão. |
| `revolucao.py` | As bolinhas de papel que o pet atira no cursor quando está em revolução. |
| `segundo_pet.py` | Suporte opcional a um 2º personagem na tela ao mesmo tempo, interagindo com o pet principal (brincam juntos ou brigam/trombam). |
| `sleep.py` | Quando ele dorme, quando acorda, e o que acontece ao adormecer. |
