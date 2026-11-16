# Prime-Ulam LDPC

Família de códigos de correção de apagamentos gerada inteiramente por fórmula: um número primo e cerca de 70 inteiros pequenos descrevem um código completo, sem tabelas nem matrizes armazenadas. A construção nasceu da geometria da espiral de Ulam e evoluiu para uma estrutura algébrica módulo um primo, com zero ciclos de comprimento 4 garantidos por teorema.

**Estado (novembro de 2026):** construção final (v5+G) definida e medida contra 5G NR, PEG, Reed–Solomon e RaptorQ. Repositório privado; decisão sobre propriedade intelectual pendente. Relatório completo em [`docs/relatorio_tecnico.md`](docs/relatorio_tecnico.md).

## Resultado em uma tabela (taxa 0,80, canal de apagamento)

| Critério | Prime-Ulam v5+G | 5G NR LDPC | RaptorQ |
| --- | --- | --- | --- |
| Falha a 19% de perda, bloco de 1.480 símbolos | 1,3e-4 | 1,9e-3 | ~0 |
| Falha a 17,5% de perda, 150.000 padrões | 0 | 10 | 0 |
| Decodificação a 15% de perda (símbolos de 1 KB) | 2,5 a 3,7 GB/s, só XOR | semelhante | ~1 GB/s nativo publicado |
| Decodificação a 19% de perda | 0,3 a 0,85 GB/s | mais lenta | ~1 GB/s |
| Descrição do código | um primo + ~70 inteiros | tabelas padronizadas | tabelas + gerador |
| Recuperação no limite exato (20%) | falha | falha | 99,5% |

O Prime-Ulam ganha do 5G NR em recuperação e simplicidade; perde do RaptorQ e do Reed–Solomon em garantia de recuperação perto do limite. O nicho é perda moderada (até ~15%), processador modesto e tamanhos de bloco fora dos padrões: satélites pequenos, IoT, armazenamento de borda.

## A construção em cinco linhas

- **Dados:** 32 braços × p posições radiais (p primo > 32); 2 braços não são transmitidos.
- **Equações esparsas:** 10 famílias de espirais; o dado (i, j) entra na equação `10·((a_c·((j + s_c·i) mod p) + b_c) mod p) + c` para cada família c do seu braço. Zero ciclos-4 porque p é primo.
- **Paridade:** acumulador de cadeia fechada; 16 paridades esparsas não são transmitidas.
- **Pré-código denso:** 16 equações; o dado (i, j) entra na equação k se `(i − a_k)² + (j − b_k)² mod p` é resíduo quadrático (norma de inteiro gaussiano).
- **Transmissão:** n = 40p símbolos, taxa 0,80, ordem dada por dois inteiros g e h.

## Estrutura do repositório

```
docs/        relatorio_tecnico.md (+ .pdf), briefing de novembro de 2026 (ponto de partida)
src/
  construction/  pu3.py (v3 regular), v4.py, v5.py (irregular), fair.py (v5+G, construção final), gauss_dense.py
  benchmarks/    compare.py (5G NR + PEG), validate5g.py (contra Sionna), floor.py, burst_eq.py,
                 cost_ops.py, rq_bench.py, rq_time.py (RaptorQ), diag.py, dense16.py, v6.py
  decoder/       pudec.c (decodificador em C), export_code.py, xorbw.c
  early/         primeira geração (matrizes 64×256 armazenadas): sim.py, test16.py, ctrl.py, improve.py
data/
  codes/     parâmetros de cada versão (v5_p37.json, v5_p127.json, ...) e códigos exportados (code_p37.txt, code_p127.txt)
  5g/        grafos-base do 5G NR (TS 38.212), extraídos do pacote Sionna
  matrices/  matrizes da primeira geração (xlsx)
results/     saídas brutas (json e log) de todos os experimentos citados no relatório
```

## Reproduzir

Requisitos: Python 3.10+, `numpy`, `openpyxl`; opcionais `sionna` (validação do 5G) e `raptorq` (benchmark RaptorQ); gcc para o decodificador.

```bash
pip install numpy openpyxl            # base
pip install sionna raptorq            # opcionais

# verificação independente: reconstrói o código a partir das fórmulas do artigo e compara com data/codes/
python3 -I src/verify/verify_article.py 37 127

# construção final em taxa idêntica, p = 37, 2.000 padrões
python3 -I src/construction/fair.py src/construction data/5g 37 2000 0.175,0.19,0.195

# piso de erro (código 0 = Prime-Ulam, 1 = 5G NR, 2 = PEG)
python3 -I src/benchmarks/floor.py src/construction data/5g 37 20000 0.15,0.175 0

# decodificador em C: tempo e XORs por símbolo
gcc -O3 -march=native -o pudec src/decoder/pudec.c
./pudec data/codes/code_p37.txt 1024 200 0.10,0.15,0.17,0.19

# validar a montagem do 5G NR contra o Sionna
python3 -I src/benchmarks/validate5g.py
```

Os scripts recebem como primeiro argumento a pasta de construção (`src/construction`, que contém cópias dos JSON de parâmetros) e como segundo a pasta das tabelas 5G (`data/5g`). Todas as sementes são fixas. Os três comandos acima foram verificados a partir da raiz do repositório.

## Licença

Código, dados, relatório e artigo são dedicados ao domínio público pela [CC0 1.0 Universal](LICENSE). Nenhum direito autoral é reservado; o uso é livre, inclusive comercial. A licença não concede direitos sobre marcas nem sobre patentes de terceiros.
