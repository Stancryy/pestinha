# `ferramentas/` — geradores de documentação

> Gerado por `ferramentas/gerar_readmes.py` a partir das docstrings. Não edite à mão: rode o script.

Rode depois de mudar módulos ou a rede, para a documentação não desatualizar:

```bash
python ferramentas/gerar_readmes.py
python ferramentas/gerar_doc_rede.py
```

- `fuzz_pestinha.py` roda o app com ações aleatórias e checa invariantes:
  `python -B ferramentas/fuzz_pestinha.py 150 80` (rodadas, ações por rodada).
- `medir_cartazes.py` confere se cada frase cabe na placa (rode no Windows, com as fontes reais).

| Arquivo | O que faz |
|---|---|
| `benchmark.py` | Benchmark de desempenho do Pestinha: abertura, rede neural, ciclos think/frame, RAM e tamanho de assets. |
| `fuzz_pestinha.py` | Roda o app inteiro com relógio virtual e ações aleatórias, checando invariantes. |
| `gerar_doc_rede.py` | Gera docs/REDE_NEURAL.md a partir do código (canais, interneurônios, motores, conexões e limiares). |
| `gerar_mia_zuric.py` | Gera os arquivos de configuração, falas (recadinhos, bilhetes tristes, cartazes) e memes originais em pixel art/WebP das personagens Mia (pets/mia*) e Zuric (pets/zuric*). |
| `gerar_panfleto.py` | Desenha pets/jorge/bolinha_papel.png: um panfleto de mentoria amassado, que o Jorge atira na revolução. |
| `gerar_readmes.py` | Gera pestinha/README.md e o README de cada camada a partir das docstrings dos módulos. |
| `medir_cartazes.py` | Mede se cada frase do cartazes.txt de cada pet cabe na placa em que aparece, com as fontes de verdade. |
