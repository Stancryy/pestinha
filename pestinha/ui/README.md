# `pestinha/ui/`

> Gerado por `ferramentas/gerar_readmes.py` a partir das docstrings. Não edite à mão: rode o script.

Janelas de interface: tela de permissões, bandeja, passo a passo, monitor neural e painel de protesto.

**Pode importar de:** core, sense, body, world, mind (e dos módulos compartilhados). A regra é verificada por `tests/test_arquitetura.py`.

| Arquivo | O que faz |
|---|---|
| `diario_panel.py` | Painel local com o histórico de humor (lido de `timeline.csv` + sessão atual) e a vitrine de conquistas (`Conquistas`). |
| `ferramentas_ui.py` | Diálogos de Ajustes Finos (`ajustes.py`), Editor de Programas (`ACTIVITY_APPS`) e Assistente (Wizard) de Criação de Personagem. |
| `float_manager.py` | Os painéis flutuantes (monitor neural e painel de protesto). |
| `monitor.py` | O que a rede está fazendo agora, sincronizado com o corpo. |
| `onboarding.py` | Passo a passo da primeira vez, com aviso de projeto em desenvolvimento. |
| `panel.py` | Medidor de protesto: quanto falta para ele entrar em greve. |
| `rotulos.py` | Os nomes que aparecem na tela, em português. |
| `ui.py` | Tela inicial de permissões, ícone na bandeja e atalho de pânico. |
