# Histórico de versões

## 0.8.0 — Versão Personalizada (Mia)

### Limpeza e base (Etapa 1)

- Pasta `executáveis/` removida do rastreamento do Git e adicionada ao `.gitignore` (mantendo os arquivos locais intactos; builds vão para Releases).
- Metadados do `pyproject.toml` atualizados (versão `0.8.0` e descrição multiplataforma) e texto da licença de `assets/` e `pets/` completado no `README.md`.
- Compatibilidade limpa com Python 3.14 (`shutil.rmtree` atualizado para usar `onexc` sem aviso de depreciação).

### Log rotativo, crash report e qualidade (Etapa 2)

- Rotação por tamanho em `memory/logs/pestinha.log` (mantendo backups `.1`, `.2`, `.3` e as linhas recentes no arquivo ativo).
- Relatório local de travamento (`memory/logs/crash.log`) via `sys.excepthook`, sem dados de janelas e respeitando `desligar_arquivo()`.
- Configuração de `ruff`, `mypy`, `pytest-cov` e `.pre-commit-config.yaml`.

### Otimização, WebP, cache e FPS adaptativo (Etapa 3)

- Script `ferramentas/benchmark.py` para medir tempo de abertura, passo da rede neural, ciclos `frame`/`think`, RAM e tamanho de assets.
- Imagens de `assets/comum/` convertidas para `.webp` e redimensionadas (**1.706,5 KB → 9,3 KB**, redução de 99,4%), com `ConteudoPaths.resolver_imagem` suportando `.webp` e `.png`.
- Cache em memória de `QPixmap` (`carregar_pixmap`) para bolinhas, notebook e memes.
- Otimização de `LIFBrain.step` com linhas esparsas ativas e `np.add.reduceat` (~1,7x mais rápido e 100% equivalente matematicamente).
- FPS adaptativo em `PestinhaApp`: ~60 fps em movimento (`16 ms`), ~20 fps parado (`50 ms`), ~5 fps dormindo (`200 ms`).

### Personagem Mia com 15 sprites pixel-art e memes (Etapa 6)
- Substituição de Bryan e Jorge pela personagem **Mia** (`pets/mia.json` e `pets/mia/`), com estética anime pixel-art (cabelo rosa pastel com pontas azul-ciano, olhos rubi/magenta, gargantilha vermelha e lacinho).
- Suporte a sprites de rosto pixel-art por emoção em `pestinha/body/desenho_rosto.py` (`sprites/<emocao>.webp`, renderizados com `SmoothPixmapTransform=False` para manter os pixels nítidos) e 15 expressões completas recortadas da folha de referência da Mia (`observando`, `feliz`, `carinho`, `suando`, `trabalhando`, `triste`, `chorando_1`, `chorando_2`, `dramatico`, `curioso`, `assustado`, `chocado`, `contente`, `dormindo`, `bravo`).
- Textos personalizados (`recadinhos.txt`, `recadinhos_tristes.txt`, `cartazes.txt`), `bolinha_papel.webp` e 27 memes em `.webp` distribuídos em 9 pastas de emoção.

### Instância única, Iniciar com o Windows, Atalhos e Não Perturbe (Etapa 7)
- Trava de instância única (`memory/pestinha.lock`) com recuperação automática se o processo anterior não existir mais.
- Opção opcional `"Iniciar junto com o Windows"` que cria/remove `Pestinha.vbs` na pasta `Startup` do usuário abrindo com `--direto`.
- Atalho global de pânico configurável (`atalho_panico`) na tela de configurações.
- Modo `"Não Perturbe"` automático (em jogos `GAMING`, tela cheia ou reuniões como Zoom/Teams) e manual pelo menu da bandeja, pausando travessuras e escondendo a bolinha.

### Interfaces de Ajustes Finos, Editor de Programas e Wizard de Personagem (Etapa 8)
- Tela de Ajustes Finos (`AjustesDialog` em `pestinha/ui/ferramentas_ui.py`) para todos os números de `pestinha/ajustes.py`, validados por `_LIMITES` e salvos em `memory/ajustes.json` com botão de restauração.
- Editor visual de programas por atividade (`AtividadesDialog`), permitindo adicionar programas e categorias personalizadas em `memory/activities.json`.
- Assistente de criação de personagem (`WizardPetDialog` e `config.criar_pet_personalizado`), gerando `pets/<id>.json` e a estrutura de pastas e textos iniciais.

### Ambiente Vivo: Ciclo de Rotina, CPU/RAM, Música e Barra de Tarefas (Etapa 9)
- Ciclo dia/noite adaptativo à rotina aprendida (`fator_ciclo_rotina` em `pestinha/sense/timeline.py`), ajustando o gasto de energia conforme seus horários reais de atividade em vez de horários fixos.
- Reação opcional (`reagir_hardware`, desligada por padrão) ao uso de CPU (`suando`, usando o sprite `suando.webp` da Mia) e RAM (`apertado`), com limites configuráveis em `ajustes.py`.
- Reação opcional (`reagir_musica`, desligada por padrão) à música tocando, fazendo a Mia dançar no ritmo e exibindo notas musicais (`♪ ♫`) sem nunca ler títulos de mídia.
- Suporte explícito a andar e pousar na borda da barra de tarefas (`pousar_barra_tarefas`).

### Companhia de Programação: Pomodoro, Lembretes e Commits Git (Etapa 10)
- Modo Pomodoro/Foco (`CompanhiaController` em `pestinha/mind/companhia.py` e opção no menu do pet): a Mia trabalha junto no notebook e sugere pausas leves ao fim do ciclo.
- Lembretes opcionais de água e postura (`lembretes_saude`, desligado por padrão), com mensagens gentis e sem pressão.
- Comemoração opcional de commits locais do Git (`comemorar_commits`, desligado por padrão, e `git_repo_path` configurável), lendo apenas o `st_mtime` de `.git/logs/HEAD` sem nunca abrir nem ler o conteúdo.

### Skins Sazonais, Efeitos Sonoros, Conquistas e Diário do Pet (Etapa 11)
- Acessórios sazonais automáticos (`acessorio_sazonal` e `aplicar_skin_sazonal` em `pestinha/body/desenho_rosto.py`): gorro de Natal em dezembro, chifrinhos no Halloween e chapéu de festa no aniversário do pet.
- Efeitos sonoros retrô 8-bit opcionais (`SoundFX` em `pestinha/world/som.py`, desligados por padrão) sintetizados em memória, com controle de volume (`0..100%`) e respeito ao modo Não Perturbe.
- Sistema de conquistas (`Conquistas` em `pestinha/core/conquistas.py`, salvo em `memory/pets/<id>/achievements.json`).
- Painel local **"Diário do Pet"** (`DiarioPanel` em `pestinha/ui/diario_panel.py`), acessível pela bandeja e pelo menu da Mia, exibindo distribuição de humor e progresso das conquistas.

### 2º Pet Simultâneo e Frases por LLM Local (Etapa 12)
- Suporte opcional a um 2º pet simultâneo na tela (`SegundoPetController` em `pestinha/mind/segundo_pet.py` e permissão `segundo_pet_ativo`), que passeia, persegue a bolinha e interage com a Mia (brincam juntos quando calmos ou brigam/trombam em protesto) quando outro personagem é criado pelo assistente.
- Geração opcional e 100% offline de frases de post-it por LLM local (`GeradorLLMLocal` em `pestinha/mind/llm_local.py`, suportando Ollama em `127.0.0.1:11434` e LM Studio / OpenAI local em `127.0.0.1:1234`), validando estritamente endereços de loopback (`127.0.0.1`, `localhost`, `::1`) e caindo imediatamente para os arquivos `.txt` quando desligado ou indisponível.

### Build `--onedir` com ícone da Mia e metadados de versão (Etapa 13 / Fase 4)
- Script `ferramentas/empacotar.py` que converte `pets/mia/sprites/feliz.webp` em `assets/comum/icone_mia.ico` multi-resolução (`16x16` a `256x256`), gera metadados de versão `0.8.0.0` do Windows e compila `executáveis/Pestinha/Pestinha.exe` no modo `--onedir` com cópia integrada de `assets/` e `pets/`.

### Expansão da SNN: Novos Sentidos e Comportamentos (Fase 1)
- Expansão da rede neural pulsada para **506 neurônios**, **16.687 sinapses** e **36 canais sensoriais** (6 novos canais de 6 neurônios cada).
- Novos canais com modelagem biológica de habituação:
  - `TYPING_SPEED` (velocidade de digitação agregada, d=0.0001, tau_rec=900 s): monitor anônimo que afeta FOCUS, ALERT e desperta euforia/torcida.
  - `CPU_LOAD` (carga de CPU, ambiental sem habituação): afeta ALERT e FRUSTRATION, gerando animação ofegante/suor e reações a aquecimento.
  - `CIRCADIAN` (ritmo circadiano noturno/madrugada, ciclo biológico): afeta TIRED e QUIET, elevando o motor DROWSE e bocejos.
  - `MOUSE_SPEED` (velocidade do cursor, d=0.0004, tau_rec=600 s): afeta ALERT e CURIOUS, reagindo a movimentos bruscos do mouse próximo ao pet.
  - `BATTERY_LOW` (bateria baixa sem tomada em notebooks, urgência): afeta ALERT e GLOOM, gerando tremor leve e alertas de tomada.
  - `WINDOW_COUNT` (multitarefa com muitas janelas abertas, d=0.0002, tau_rec=1200 s): estimula CURIOUS e ALERT.
- Validações completas em `pestinha/ajustes.py` (`LIMIAR_DIGITACAO_RAPIDA`, `LIMIAR_MOUSE_RAPIDO`, `LIMIAR_BATERIA_BAIXA`, `LIMIAR_JANELAS_MUITAS`).
- Calibração de alegria moderada (`CHEER` em ~1.5 - 2.0 Hz durante digitação) e desacoplamento de digitação com o notebook.
- Persistência permanente do estado do notebook escondido (`notebook_escondido` em `memory/permissions.json`), garantindo que o notebook nunca reapareça do nada nem atraia o pet quando escondido pelo usuário.
- Conformidade estrita de privacidade em `PRIVACIDADE.md` (zero registro de teclas ou títulos de janelas).
- Suíte completa de testes (`tests/test_novos_sensores.py` e `tests/test_notebook_persistencia.py`) e regeneração automática de `docs/REDE_NEURAL.md`.

## Suporte a macOS e Linux

- Toda a leitura do sistema (programa em primeiro plano, tempo ocioso, janelas, tela cheia, foco e o atalho
  de pânico) passa para `pestinha/plataforma/`, com um módulo por sistema. O resto do código não sabe
  qual sistema está rodando.
- O Windows continua com o mesmo comportamento: o código foi movido, não reescrito.
- macOS: Quartz e AppKit (pyobjc), tempo ocioso pelo `ioreg` se não houver pyobjc. Atalho via pynput.
- Linux (X11): xdotool, wmctrl e xprintidle; atalho via pynput. Em Wayland, o pet não enxerga janelas
  nem o tempo ocioso, e o atalho não funciona.
- A checagem de atividade reconhece os nomes de programa dos três sistemas (com ou sem `.exe`).

## Renomeação para Pestinha

- O programa e o pacote Python passam a se chamar `pestinha/` (antes `bryan/`); a classe principal é
  `PestinhaApp`; o executável, o log e a documentação usam Pestinha.
- Bryan continua sendo o nome do primeiro personagem: `pets/bryan.json`, `pets/bryan/`, a memória
  `memory/pets/bryan/` e os arquivos de conteúdo dele não mudaram.
- Os comentários e textos que falavam do pet em geral passam a dizer "o pet".

## 0.7.0 — primeira versão pública (em preparação)

### O que ele faz

- Pet de tela com corpo físico: gravidade, quique, giro, pouso nas barras de título, arraste e arremesso.
- Rede neural pulsada de 470 neurônios LIF, com 30 canais sensoriais, 10 populações de interneurônios
  e 15 motores (8 de expressão e 7 de decisão).
- Emoções vindas dos motores; carinho com olhinhos fechados de felicidade.
- Bolinha de tênis, notebook de trabalho (VS Code, Visual Studio, PyCharm, Claude, Codex) e pedido de
  trabalho que ele pode recusar.
- Travessuras com memes, fotos, post-its e bilhetes tristes, com frequência decidida pela rede.
- Protesto em estágios até a revolução contra o cursor, com cartazes e bolinhas de papel.
- Cantinho do castigo: placa arrastável, perdão por carinho, fuga por vontade acumulada, rancor, receio,
  medo condicionado da placa e cartazes de xingamento.
- Aprendizado: habituação, regra de três fatores, condicionamento Rescorla–Wagner, memória episódica.
- Pânico (`Ctrl + Alt + Shift + B`), pausa, modo teste, monitor neural e painel de protesto.

### Memória por personagem

- Cada personagem tem a sua memória em `memory/pets/<pet>/` (rede e os sete arquivos de memória); o que
  é do app (permissões, rotina, painéis, log) continua em `memory/`.
- Migração automática da versão antiga: copia, confere, guarda os originais em `memory/legado/<pet>/` e
  só então marca como migrado. Conflito ou falta de permissão não sobrescrevem nada: ele segue com os
  arquivos antigos e avisa na bandeja.

### Conteúdo por personagem

- Frases, cartazes e memes de cada personagem ficam em `pets/<pet>/`; imagens neutras (bolinhas, notebook)
  e suas fotos em `assets/comum/`. Um personagem nunca usa o conteúdo de outro: sem conteúdo próprio, usa
  frases neutras ou não faz aquela travessura.
- Os cartazes do cantinho do castigo saíram do código para as seções `[castigo]` e `[xingamento]` do
  `cartazes.txt` do pet.

### Escolha do personagem

- O programa passa a se chamar **Pestinha**; o Bryan é o primeiro personagem.
- O personagem é escolhido em Configurações (vale ao reabrir). Só `pets/<pet>.json` vira opção.
- Os textos usam o nome do personagem onde é ele que fala (apresentação, "Estou aqui", notebook, monitor
  neural, painel de protesto) e o nome do programa no resto (configurações, bandeja, pânico).
- O log passa a ser `memory/logs/pestinha.log`; o executável, `Pestinha.exe`.

### Jorge

- Segundo personagem: coach de finanças e IA, trambiqueiro. Mesma rede e mesmos estágios do Bryan, com
  outra semente, outro temperamento e conteúdo próprio (recadinhos, bilhetes tristes, cartazes de todos os
  estágios e do cantinho, e um panfleto de mentoria no lugar da bolinha de papel). Cinco memes para cada uma de felizes, contentes, curiosos e bravos, em `pets/jorge/memes/`.
- `ferramentas/medir_cartazes.py` confere, com as fontes de verdade, se cada cartaz cabe na placa.
- `ferramentas/gerar_panfleto.py` desenha o panfleto do Jorge.

### Cores e acessórios

- Cada pet pode ter as próprias cores (moldura, tela, olhos) e acessórios (óculos, gravata) no campo
  `aparencia` do `.json`. Os acessórios são uma camada por cima do rosto; olhos e expressões não mudam.
- O Jorge tem moldura e olhos dourados e gravata vermelha. O Bryan continua igual.

### Licença

- Código sob GPL-3.0-or-later (`LICENSE`).

### Qualidade

- Arquitetura em camadas verificada por teste; `app.py` dividido em composição e mixins de sessão e
  interação.
- Persistência validada: escrita atômica, recusa de `NaN`, carga tudo-ou-nada.
- Cinco rodadas de auditoria, com cada bug corrigido coberto por teste, registradas em `docs/auditorias/`.
- Suíte de testes, bateria de 100 cenários do cantinho e fuzzer com invariantes.
