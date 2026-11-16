# Prime-Ulam LDPC — Relatório técnico

16 de novembro de 2026 · Karlos Marden Maia (Kayros Consulting LLC)

## Resumo executivo

O Prime-Ulam LDPC é uma família de códigos de correção de apagamentos gerada inteiramente por fórmula: um número primo e cerca de 70 inteiros pequenos descrevem um código completo, sem tabelas nem matrizes armazenadas. Na versão final, em canal de apagamento e taxa 0,80, o código recupera os dados com falha abaixo de 1 em 150.000 a 17,5% de perdas, supera o LDPC do padrão 5G NR em todas as faixas medidas, e decodifica a 2,5 a 3,7 GB/s em perdas de até 15%, usando apenas operações XOR.

A ideia nasceu de uma pergunta geométrica: a espiral de Ulam, que organiza os inteiros em um plano e revela alinhamentos entre os números primos, poderia organizar também as equações de um código corretor? A resposta que a pesquisa encontrou foi mais precisa do que a pergunta: o que importa não é a posição dos primos na espiral, mas o primo como módulo da aritmética que define as conexões. Com esse princípio, a geometria passou a garantir, por construção, a ausência dos ciclos curtos que degradam qualquer código LDPC.

O relatório apresenta a evolução da ideia, a construção final, os resultados medidos contra 5G NR, PEG, Reed–Solomon e RaptorQ, e o posicionamento científico e comercial. A conclusão é equilibrada: o Prime-Ulam não alcança a garantia de recuperação do RaptorQ e do Reed–Solomon, que são ótimos nessa métrica, mas ocupa um espaço próprio onde simplicidade, velocidade de decodificação em perdas moderadas e descrição compacta valem mais do que o último décimo de ponto percentual de recuperação.

## 1. O problema: recuperar o que se perdeu sem pedir de novo

Em muitos sistemas de comunicação e armazenamento, os dados não chegam corrompidos: chegam faltando. Um pacote de rede é descartado, um setor de disco falha, um satélite sai da linha de visada por alguns milissegundos. O receptor sabe exatamente o que faltou, mas não sabe o conteúdo. Esse é o canal de apagamento, e os códigos que o atendem são chamados de códigos de apagamento.

A solução clássica é enviar redundância: além dos k blocos de dados, enviam-se m blocos de paridade, cada um calculado como a soma XOR de um subconjunto dos dados. Se alguns blocos se perdem, os que chegaram formam um sistema de equações lineares sobre o corpo binário, e resolver esse sistema reconstrói o que faltou. A taxa do código é k dividido por k + m; neste trabalho ela é fixada em 0,80, ou seja, 20% de redundância.

O limite teórico é simples: com m paridades, é impossível recuperar mais de m blocos perdidos. Um código é bom quando chega perto desse limite com três propriedades ao mesmo tempo:

1. **Recuperação alta**, para que quase todo padrão de perda abaixo do limite seja resolvido.
2. **Decodificação barata**, de preferência por "peeling": encontrar uma equação com uma única incógnita, resolvê-la, substituir e repetir, sem nunca montar uma matriz.
3. **Descrição compacta**, para que o código caiba em hardware simples e possa ser gerado para qualquer tamanho de bloco.

Os códigos LDPC (de matriz esparsa) atendem às duas primeiras quando a matriz é bem projetada. O que degrada um LDPC são os ciclos curtos: dois dados que participam das mesmas duas equações formam um ciclo de comprimento quatro, e esses ciclos criam dependências que impedem a recuperação. Projetar a matriz é, em grande parte, a arte de evitar esses ciclos. A contribuição central do Prime-Ulam está exatamente aí: uma regra geométrica que os elimina por construção.

## 2. Como a ideia nasceu e evoluiu

A ideia partiu de uma observação conhecida da teoria dos números. Quando os inteiros são escritos em espiral a partir do centro de uma grade, os primos se alinham em diagonais e braços, um padrão descoberto por Stanislaw Ulam em 1963. A pergunta que deu origem ao projeto foi: se os primos se organizam no plano de forma tão pouco aleatória e tão pouco regular, essa organização poderia servir para escolher quais dados entram em cada equação de paridade?

A evolução se deu em cinco etapas, cada uma preservando o que a anterior havia estabelecido:

| Etapa | O que foi feito | Resultado |
| --- | --- | --- |
| 1. Geometria como regra de conexão | coordenadas da espiral de Ulam definem as equações | 97,4% de recuperação a 15% de perda |
| 2. O primo como módulo | com lado primo, duas espirais se cruzam em um só ponto | zero ciclos-4, por teorema |
| 3. Tudo por fórmula | 14 inteiros descrevem o código; paridade em acumulador | iguala o PEG, sem matriz armazenada |
| 4. Irregularidade e braços não transmitidos | 32 braços, 10 famílias de espirais, cadeia fechada | nível do 5G NR |
| 5. Pré-código gaussiano | norma de inteiros gaussianos mod p define as equações densas | supera o 5G NR em taxa idêntica |

Cada etapa preservou a anterior: a geometria virou teorema, o teorema virou fórmula, e a fórmula recebeu irregularidade e um pré-código.

**Etapa 1 — Geometria como regra de conexão.** As primeiras matrizes usaram as coordenadas dos pontos na espiral (x, y, x + y, x − y) para definir as equações, com braços, pareamentos antípodas e ponderações radiais. Essa fase estabeleceu a tese de trabalho: a topologia da matriz, e não os pesos, decide o desempenho. Um único rearranjo dos pares antípodas levou a recuperação de 4% para 95%, enquanto ajustes de pesos moviam décimos de ponto. A otimização algébrica dessas matrizes (remoção de ciclos curtos) chegou a 97,4% de recuperação com 15% de perdas em blocos de 320 bits.

**Etapa 2 — O primo como módulo.** O avanço decisivo veio ao perguntar por que a geometria funcionava. A resposta: quando a grade tem lado primo, duas retas de inclinações diferentes se cruzam em no máximo um ponto, módulo p. Com lado 16, a mesma regra produz 128 ciclos de comprimento quatro; com lado 17, nenhum. O que a espiral de Ulam sugeria por imagem, a aritmética modular garante por teorema. A construção passou a ser: 16 braços com p posições radiais, quatro famílias de espirais com passos distintos, e cada equação reúne os pontos em que raio + passo × braço dá o mesmo valor módulo p.

**Etapa 3 — Tudo por fórmula.** Com a regra algébrica, a matriz deixou de ser armazenada. Um primo, quatro passos, oito coeficientes para a posição das equações na cadeia de paridade e dois inteiros para a ordem de transmissão descrevem o código inteiro. A paridade adotou a forma de acumulador (cada paridade entra em duas equações consecutivas), que dobra a proteção de cada bit de paridade sem custo. Essa versão igualou o melhor método genérico de projeto (PEG) em todos os tamanhos, com 14 inteiros em vez de milhares de índices.

**Etapa 4 — Irregularidade e braços não transmitidos.** Os melhores códigos modernos dão graus diferentes a bits diferentes: alguns participam de muitas equações, a maioria de poucas. A construção foi ampliada para 32 braços e 10 famílias de espirais, com dois braços de grau alto que não são transmitidos (o receptor os reconstrói) e 30 braços leves de grau 3. A cadeia de paridade foi fechada para eliminar a ponta solta. Com isso o código alcançou o nível do 5G NR na faixa de 15% a 19,5% de perdas.

**Etapa 5 — O pré-código gaussiano.** A última peça nasceu de uma ideia geométrica nova: tratar cada ponto da espiral como um número complexo e usar o produto pelo conjugado, que é um número real, como critério de conexão. Traduzida para o corpo binário, a ideia tomou esta forma: cada ponto (braço i, raio j) é o inteiro gaussiano i + j·I módulo p; para cada equação densa escolhe-se um centro, e o ponto entra na equação se a norma da diferença, (i − a)² + (j − b)² módulo p, é resíduo quadrático. Dezesseis equações assim, com centros em progressão aritmética, substituem dezesseis paridades esparsas e eliminam o piso de erro residual, em taxa idêntica. Foi a etapa que levou o código a superar o 5G NR.

## 3. A construção final

O código final, chamado aqui de Prime-Ulam v5+G, é definido por um primo p maior que 32 e por um conjunto fixo de inteiros pequenos. Para p = 37 o bloco tem 1.480 símbolos transmitidos; para p = 127, 5.080. Qualquer primo serve, e o mesmo conjunto de parâmetros gera a família inteira.

| Elemento | Definição | Quantidade |
| --- | --- | --- |
| Dados | 32 braços × p posições radiais | k = 32p |
| Braços não transmitidos | 2 braços de grau 8, reconstruídos pelo receptor | 2p símbolos |
| Famílias de espirais | 10 famílias, cada uma com seu passo s_c | 10 |
| Equações esparsas | Uma por valor de raio + s_c × braço (módulo p), por família | 10p |
| Paridades esparsas | Acumulador de cadeia fechada; 16 delas não transmitidas | 10p − 16 transmitidas |
| Equações densas | Norma gaussiana e resíduo quadrático, centros em progressão aritmética | 16 |
| Transmitidos | 30p dados + (10p − 16) paridades esparsas + 16 densas | n = 40p |
| Taxa | k / n | 0,80 |

**Parte esparsa.** O braço i participa de um subconjunto F_i das dez famílias: os dois braços não transmitidos participam de oito, os trinta restantes de três, distribuídos de modo que cada família receba o mesmo número de braços. O dado na posição (i, j) entra, para cada família c em F_i, na equação de índice

```
q(i, j, c) = 10 · ( a_c · ((j + s_c · i) mod p) + b_c  mod p ) + c
```

onde a_c e b_c são os coeficientes que posicionam a equação na cadeia de paridade. A garantia central segue de p ser primo: duas espirais de famílias distintas têm no máximo um braço em comum, logo dois dados nunca compartilham duas equações, e a matriz não tem ciclos de comprimento quatro. Isso foi verificado numericamente para p = 37 e p = 127.

**Paridade em acumulador fechado.** A paridade q entra nas equações q − 1 e q; a paridade 0 entra nas equações 0, M/2 e M − 1, fechando a cadeia. Com isso toda paridade está protegida por duas equações e a codificação continua sequencial.

**Pré-código denso.** A equação densa k, com centro (a_k, b_k) = (5k mod p, 7k + 1 mod p), contém o dado (i, j) quando

```
(i − a_k)² + (j − b_k)²  mod p  ∈  { x² mod p : 1 ≤ x < p }
```

Cada equação densa contém cerca de metade dos dados e gera uma paridade transmitida no lugar de uma paridade esparsa perfurada. É a tradução binária da ideia do produto complexo pelo conjugado: a norma do inteiro gaussiano decide a conexão.

**Ordem de transmissão.** Os símbolos são enviados no padrão "quatro dados, uma paridade"; o t-ésimo dado ocupa o braço t mod 32 e o raio g·t mod p, e a q-ésima paridade é a de índice h·q mod M. Os inteiros g e h são escolhidos para maximizar o comprimento de rajada sempre recuperável.

**Decodificação.** Primeiro o peeling nas equações esparsas; quando ele trava, as incógnitas restantes formam um sistema pequeno, resolvido por eliminação em GF(2) com as equações densas incluídas. Tudo é XOR de pacotes.

**Parâmetros completos.** Os valores de s_c, a_c, b_c, F_i, g e h usados nos testes estão em `data/codes/v5_p37.json` e `data/codes/v5_p127.json`, e o código exportado para o decodificador está em `data/codes/code_p37.txt` e `data/codes/code_p127.txt`. São cerca de 70 inteiros ao todo.

## 4. Resultados

Todos os números abaixo vêm de simulação em canal de apagamento, com decodificação exata por posto em GF(2), os mesmos padrões de perda aplicados a todos os códigos comparados, e taxa 0,80 em todos. "Falha" significa que ao menos um símbolo não pôde ser reconstruído.

**Recuperação em taxa idêntica.** A tabela compara o Prime-Ulam v5+G com o LDPC do padrão 5G NR (TS 38.212, montado a partir das tabelas oficiais e validado contra o codificador de referência Sionna), nos mesmos k e n.

| Bloco | Perda | Padrões | Prime-Ulam v5+G | 5G NR |
| --- | --- | --- | --- | --- |
| 1.480 símbolos | 17,5% | 150.000 | 0 falhas | 10 falhas (6,7e-5) |
| 1.480 símbolos | 19,0% | 150.000 | 19 falhas (1,3e-4) | 285 falhas (1,9e-3) |
| 1.480 símbolos | 19,5% | 150.000 | 2,4% de falhas | 10,7% de falhas |
| 5.080 símbolos | 17,5% | 15.000 | 0 falhas | 0 falhas |
| 5.080 símbolos | 19,0% | 15.000 | 0 falhas | 0 falhas |
| 5.080 símbolos | 19,5% | 15.000 | 0 falhas | 9 falhas (6,0e-4) |

O limite teórico de perda é 20%. A 19% de perda em 1.480 símbolos, o Prime-Ulam falha 15 vezes menos que o 5G NR; a 19,5%, 4,5 vezes menos.

**Piso de erro.** Com 400.000 padrões a 15% e 17,5% de perda em 1.480 símbolos, a versão sem pré-código apresentava um piso de cerca de 1e-4 a 5e-4, causado por palavras-código de peso baixo formadas por dados de grau 3. O pré-código gaussiano eliminou esse piso: 0 falhas em 150.000 a 17,5% e 0 em 100.000 a 19% e 19,5% na versão com 16 equações acrescentadas. A comparação com equações densas aleatórias mostrou que a construção geométrica é igual ou melhor (0 a 1 falha contra 6, com 8 equações, em 200.000 padrões).

**Rajadas.** A ordem de transmissão projetada por fórmula garante a recuperação de qualquer rajada cíclica de até 285 símbolos consecutivos em 1.480 (limite teórico 296) e de até 1.006 em 5.080 (limite 1.016, medido em amostra de inícios). Quando o 5G NR e o PEG recebem a mesma busca de ordem de envio, chegam a valores equivalentes (287 e 282 em 1.480), o que mostra que a robustez a rajadas é uma propriedade do intercalador, disponível a qualquer código bom, e não um diferencial exclusivo.

**Custo de decodificação.** Um decodificador em C, sem SIMD explícito, com símbolos de 1 KB, numa máquina virtual com Xeon a 2,1 GHz:

| Perda | 1.480 símbolos (1,2 MB) | 5.080 símbolos (4,2 MB) | XORs por símbolo de dados |
| --- | --- | --- | --- |
| 10% | 0,33 ms (3,7 GB/s) | 1,5 ms (2,8 GB/s) | 4,7 |
| 15% | 0,46 ms (2,6 GB/s) | 1,7 ms (2,5 GB/s) | 5,2 a 5,6 |
| 17% | 0,99 ms (1,2 GB/s) | 5,4 ms (0,77 GB/s) | 15 a 19 |
| 19% | 1,43 ms (0,85 GB/s) | 13,4 ms (0,31 GB/s) | 28 a 55 |

Até 15% de perda o peeling resolve quase tudo com cinco XORs por símbolo. Perto do limite, a eliminação em GF(2) domina e o custo sobe uma ordem de grandeza.

**Escalabilidade.** O desempenho melhora com o tamanho do bloco: em 5.140 símbolos a versão regular por fórmula já recuperava 100% a 19%, e a versão final não apresentou falhas até 19,5% em 15.000 padrões. O custo de geração do código para um novo tamanho é trocar o primo.

## 5. Posicionamento frente aos códigos estabelecidos

Quatro referências foram medidas no mesmo protocolo: o LDPC do 5G NR, o PEG (melhor método genérico de projeto de matrizes esparsas), o Reed–Solomon e o RaptorQ (RFC 6330, biblioteca de referência em Rust). A tabela resume o que cada um oferece.

| Critério | Prime-Ulam v5+G | 5G NR LDPC | PEG regular | Reed–Solomon | RaptorQ |
| --- | --- | --- | --- | --- | --- |
| Recuperação a 19% (1.480 símb.) | 1,3e-4 de falha | 1,9e-3 | 5,7e-2 | 0 (ótimo) | ~0 (1/256 por símbolo de folga) |
| Recuperação no limite exato (20%) | falha | falha | falha | 100% | 99,5% |
| Decodificação a 15% de perda | 2,5 a 3,7 GB/s, só XOR | semelhante, só XOR | semelhante | aritmética em GF(256), mais lenta | ~1 GB/s nativo publicado |
| Decodificação a 19% de perda | 0,3 a 0,85 GB/s | mais lenta que Prime-Ulam | semelhante | igual à de 15% | ~1 GB/s, independente da perda |
| Descrição do código | um primo + ~70 inteiros | tabelas padronizadas | matriz armazenada | um polinômio gerador | tabelas + gerador pseudoaleatório |
| Tamanhos de bloco | 40p, p primo | 51 valores de Z, dois grafos-base | qualquer | até 255 símbolos em GF(256) | qualquer k |
| Taxa | fixa 0,80 (generalizável) | ajustável por perfuração | fixa | ajustável | sem taxa (gera símbolos sob demanda) |
| Ciclos-4 | zero, por teorema | zero, por projeto | zero, por algoritmo | não se aplica | não se aplica |
| Hardware | XOR e um pequeno sistema linear | XOR; ASICs disponíveis | XOR | multiplicadores em corpo finito | XOR + GF(256) na parte densa |
| Propriedade intelectual | aberta, construções conhecidas | padrão 3GPP, patentes essenciais | aberta | aberta | patentes da Qualcomm envolvidas |

**Visão científica.** Em recuperação pura, Reed–Solomon e RaptorQ são ótimos ou quase ótimos: recuperam qualquer padrão até o limite teórico. Nenhum LDPC binário, incluindo o Prime-Ulam e o 5G NR, chega a isso, porque equações esparsas sobre o corpo binário admitem dependências que um corpo maior evita. Dentro da classe dos LDPC binários, o Prime-Ulam v5+G é o melhor dos três medidos, com margem de 4 a 15 vezes sobre o 5G NR perto do limite.

**Visão comercial.** O código com menor taxa de falha não é necessariamente o mais adotado. O LDPC do 5G NR é o mais usado do mundo não por ser o melhor em canal de apagamento, mas porque foi padronizado, tem hardware dedicado, foi otimizado para canais com ruído (seu uso real) e oferece interoperabilidade garantida. O RaptorQ domina a distribuição de arquivos e o streaming por ser sem taxa e ter garantia de recuperação, mesmo com licenciamento. O Reed–Solomon domina o armazenamento por ser ótimo e antigo o bastante para não ter patentes.

Nesse quadro, o Prime-Ulam se posiciona pelas propriedades que os três não combinam ao mesmo tempo:

- **Descrição por fórmula.** Nenhuma tabela, nenhuma matriz; o código para um bloco novo é um primo novo. Isso importa em dispositivos sem memória para tabelas e em sistemas que precisam de tamanhos de bloco fora dos padrões.
- **Decodificação por XOR com peeling dominante.** Em perdas de até 15%, cinco XORs por símbolo bastam. Processadores simples, sem multiplicador de corpo finito, decodificam a velocidade de memória.
- **Garantias por teorema.** A ausência de ciclos-4 é demonstrável, não verificada caso a caso. Isso simplifica certificação e análise.
- **Ausência de licenciamento conhecido.** As construções usadas são de domínio público há décadas.

**Prós e contras, em resumo.** O Prime-Ulam ganha do 5G NR em recuperação e em simplicidade de descrição; perde para ele em ecossistema, hardware pronto e flexibilidade de taxa. Ganha do RaptorQ em velocidade com perdas baixas e em ausência de licença; perde para ele em garantia de recuperação, em flexibilidade (taxa fixa contra sem taxa) e em velocidade perto do limite. Ganha do Reed–Solomon em custo de decodificação e em tamanho de bloco; perde em garantia de recuperação.

## 6. Originalidade: o que é conhecido e o que é novo

A honestidade sobre este ponto é o que dá credibilidade ao resto do relatório. Cada peça da construção tem um parente na literatura, e o leitor técnico vai reconhecê-los.

| Peça do Prime-Ulam | Parente na literatura | O que o Prime-Ulam acrescenta |
| --- | --- | --- |
| Espirais módulo p sem ciclos-4 | Array codes (Fan, 2000); LDPC de geometria finita (Kou, Lin, Fossorier, 2001) | Derivação geométrica a partir da espiral de Ulam; integração com as demais peças |
| Acumulador de paridade | Códigos IRA (Jin, Khandekar, McEliece, 2000) | Cadeia fechada e posicionamento por fórmula afim |
| Graus irregulares e bits não transmitidos | LDPC irregulares (Luby et al., 1998); 5G NR | Irregularidade por braço, descrita por fórmula |
| Pré-código denso | HDPC do RaptorQ (RFC 6330) | Equações densas por norma gaussiana e resíduo quadrático (construção de Paley), em vez de GF(256) |
| Intercalador por fórmula | Intercaladores afins e QPP | Escolha conjunta com a geometria do código |

Nenhuma dessas peças é inédita. O que é original é a síntese: um único objeto geométrico, o plano de inteiros módulo um primo visto como espiral, gera todas as peças de uma vez. As espirais dão a parte esparsa, a aritmética afim posiciona as equações na cadeia, a norma gaussiana dá a parte densa, e a progressão geométrica dá a ordem de transmissão. Nos códigos existentes, essas peças vêm de fontes diferentes e são ajustadas separadamente; aqui elas são funções do mesmo primo.

Três contribuições merecem ser nomeadas:

1. **O pré-código gaussiano.** Usar a norma de inteiros gaussianos módulo p com o critério de resíduo quadrático para definir equações densas de um código de apagamento é, até onde esta pesquisa alcançou, uma combinação não documentada. Ela nasceu de uma intuição geométrica (o produto pelo conjugado como coeficiente real) e se mostrou igual ou melhor que equações densas aleatórias nos testes.
2. **A trajetória metodológica.** O projeto partiu de uma hipótese sobre os primos, testou-a contra controles aleatórios, identificou o mecanismo real (o primo como módulo) e reconstruiu o código a partir dele. Esse caminho, documentado com código e dados, tem valor didático próprio.
3. **A comparação rigorosa.** Poucos trabalhos independentes comparam uma construção nova com o 5G NR validado contra implementação de referência, com PEG, com RaptorQ real e com Reed–Solomon, em taxa idêntica e com os mesmos padrões de perda. O protocolo é reproduzível e é parte da contribuição.

Em termos de criatividade, o mérito está em ter chegado a uma construção competitiva por um caminho que não é o da literatura: a literatura parte da álgebra e chega ao código; este projeto partiu de uma imagem, a espiral, e descobriu a álgebra por trás dela.

## 7. Nichos de aplicação

O perfil do Prime-Ulam é claro: perdas previsíveis e moderadas (até cerca de 15%), processador modesto, pouca memória, tamanhos de bloco fora dos padrões e necessidade de código aberto. Onde a perda chega perto do limite ou a garantia absoluta de recuperação é obrigatória, RaptorQ e Reed–Solomon continuam sendo a escolha certa. A tabela ordena os nichos do mais ao menos promissor.

| Nicho | Por que o Prime-Ulam se encaixa | Perda típica | Concorrente a vencer | Aderência |
| --- | --- | --- | --- | --- |
| Satélites pequenos (CubeSats, LEO) e enlaces terra–satélite | Processadores de bordo fracos e tolerantes a radiação; código por fórmula cabe em FPGA pequena; perdas por bloqueio e cintilação são moderadas | 5% a 15% | CCSDS (Reed–Solomon, LDPC padronizado), RaptorQ em DVB | Alta |
| Enlaces ópticos em espaço livre e intersatélite | Perdas em rajada por turbulência; intercalador por fórmula sem memória de tabela; decodificação rápida em taxa alta | 5% a 15% | Reed–Solomon, LDPC DVB-S2 | Alta |
| IoT e redes de sensores (LoRa, redes mesh, industrial) | Microcontroladores sem multiplicador de corpo finito; XOR puro; blocos pequenos gerados pelo primo | 5% a 15% | Reed–Solomon leve, repetição | Alta |
| Armazenamento distribuído e de borda com nós heterogêneos | Reconstrução por XOR é barata em nós fracos; blocos de qualquer tamanho; sem licença | 5% a 10% | Reed–Solomon (Ceph, HDFS), códigos locais de reparação | Média a alta |
| Transporte de vídeo e dados por UDP em redes privadas | Perda de pacotes moderada e previsível; decodificação a 2,5 GB/s em CPU comum; ausência de royalties | 1% a 10% | RaptorQ, FlexFEC (RTP) | Média |
| Dispositivos embarcados e automotivos | Garantias por teorema facilitam certificação; descrição auditável em poucas linhas | baixa | Reed–Solomon, CRC com retransmissão | Média |
| Pesquisa e ensino | Código completo em uma fórmula; cada propriedade tem demonstração curta; protocolo de comparação reproduzível | qualquer | nenhum | Alta |
| Telefonia celular e Wi-Fi | Padrões fechados com hardware dedicado; canal com ruído, não de apagamento | não se aplica | 5G NR, 802.11 | Baixa |
| Distribuição de arquivos em massa e broadcast | Exige sem taxa e garantia próxima de 100% | até o limite | RaptorQ | Baixa |

**O caso dos satélites de baixa órbita.** É o nicho onde todas as vantagens se somam. Um CubeSat tem um processador de poucas dezenas de MHz, memória de centenas de kilobytes e restrições severas de energia. O Prime-Ulam cabe nesse perfil: o código inteiro é gerado a partir de um primo, a decodificação em perdas de até 15% é só XOR, e a ordem de transmissão por fórmula protege contra rajadas de centenas de símbolos sem tabela de intercalação. O concorrente é o padrão CCSDS, bem estabelecido; a porta de entrada são missões universitárias e comerciais pequenas que não estão presas a ele.

**O caso do IoT.** Um microcontrolador de 32 bits decodifica um bloco de 1.480 símbolos de 32 bytes em perdas de 15% com cerca de 8.000 XORs de 32 bytes, algo em torno de um milissegundo. Nenhuma tabela precisa estar em flash. Para redes de sensores que enviam telemetria em pacotes pequenos por enlaces com perda, isso substitui retransmissões, que custam energia.

**O caso do armazenamento de borda.** Em nós de armazenamento fracos (gateways, câmeras, equipamentos industriais), reconstruir um bloco perdido por XOR é muito mais barato que por aritmética em GF(256). O Prime-Ulam permite blocos de qualquer tamanho (basta o primo) e não traz licença. A desvantagem é a taxa fixa 0,80; generalizar a taxa é trabalho futuro.

## 8. Limitações e trabalho futuro

As limitações abaixo delimitam o que os resultados sustentam. Nenhuma delas invalida as conclusões; todas indicam o que falta para um produto ou uma publicação revisada.

**Do código**

- **Taxa única.** Só a taxa 0,80 foi construída e medida. A estrutura admite outras taxas (mais famílias de espirais, mais braços), mas isso não foi feito.
- **Comprimentos discretos.** O bloco tem 40p símbolos com p primo. Tamanhos intermediários exigem encurtamento, não testado.
- **Sem garantia absoluta.** A 19% de perda em 1.480 símbolos ainda há 1,3e-4 de falha; RaptorQ e Reed–Solomon não falham aí.
- **Custo perto do limite.** Acima de 17% de perda a eliminação em GF(2) domina e o decodificador fica 3 a 10 vezes mais lento.
- **Canal de apagamento apenas.** Nada foi medido em canal com ruído (decodificação por propagação de crenças), que é o uso principal do 5G NR.

**Da medição**

- **Amostras.** As taxas de falha abaixo de 1e-5 não foram medidas; "0 falhas em 150.000" significa menos de cerca de 2e-5 com 95% de confiança.
- **Decodificador.** O decodificador em C é uma implementação direta, sem SIMD nem inativação. O RaptorQ foi medido pela interface Python, mais lenta que a biblioteca nativa; a comparação de tempo usa os números publicados da biblioteca como referência.
- **Rajadas.** A garantia em 5.080 símbolos foi medida em amostra de inícios, não em todos.
- **Parâmetros.** Coeficientes, centros e paridades perfuradas foram escolhidos por busca aleatória curta; não há prova de que sejam ótimos.

**Trabalho futuro, em ordem de valor**

1. Família de taxas (0,50 a 0,95) pela mesma fórmula, com medição em cada uma.
2. Decodificador com inativação e SIMD, para fechar a diferença de tempo perto do limite.
3. Demonstração formal da distância mínima da parte esparsa e do efeito do pré-código gaussiano.
4. Implementação em FPGA pequena e medição de energia por símbolo, voltada ao nicho de satélites.
5. Comparação com o padrão CCSDS e com códigos de reparação local usados em armazenamento.

## 9. Propriedade intelectual e publicação

A decisão entre patentear e abrir precisa vir antes de qualquer publicação, porque publicar primeiro destrói a novidade na maioria das jurisdições. Esta seção não é parecer jurídico; é o que os fatos técnicos permitem dizer, e a recomendação é consultar um agente de patentes antes de agir.

**O que pesa contra uma patente ampla.** Cada peça da construção tem parente publicado há mais de vinte anos (seção 6): array codes, códigos IRA, LDPC irregulares, pré-códigos densos, intercaladores afins. Um examinador tende a ver a síntese como combinação óbvia de técnicas conhecidas, e um concorrente poderia contornar uma patente de síntese trocando uma peça. Além disso, o mercado de códigos de apagamento é dominado por padrões abertos e por códigos de domínio público; o RaptorQ, mesmo patenteado, só se impôs porque é sem taxa e quase ótimo, propriedades que o Prime-Ulam não tem.

**O que poderia sustentar uma patente estreita.** O pré-código gaussiano (equações densas por norma de inteiros gaussianos módulo p e resíduo quadrático, acoplado a uma parte esparsa por espirais módulo o mesmo primo) é a peça com menor chance de anterioridade direta. Uma reivindicação centrada nela, mais o método de gerar código, intercalador e pré-código a partir de um único primo, é o que vale a pena submeter a uma busca de anterioridade profissional. O custo de uma busca é pequeno diante do custo de um pedido.

**Royalties são improváveis.** Mesmo com patente concedida, o licenciamento exigiria que alguém prefira pagar pelo Prime-Ulam a usar Reed–Solomon ou um LDPC aberto. Isso só aconteceria num nicho onde a vantagem de velocidade e simplicidade fosse decisiva e comprovada em hardware real, o que ainda não foi feito. O caminho mais realista para retorno é indireto: credibilidade técnica, consultoria em correção de erros para satélites e IoT, e eventual implementação sob contrato.

**Ordem recomendada**

1. Busca de anterioridade profissional sobre o pré-código gaussiano e sobre a geração integrada por um primo (semanas, custo baixo).
2. Se a busca indicar espaço: pedido provisório nos EUA, que garante a data por doze meses a custo baixo e permite publicar em seguida. O Brasil também prevê período de graça de doze meses para divulgação pelo próprio inventor, mas a maior parte da Europa e da Ásia não.
3. Se a busca não indicar espaço, ou se a decisão for abrir: publicação no GitHub com licença permissiva (decidido: CC0 1.0 para código, dados e texto, sem pedido de patente; Apache 2.0 ou MIT foram as alternativas consideradas), relatório técnico no arXiv (seção cs.IT) e registro de DOI via Zenodo. Isso cria anterioridade a seu favor, impede que terceiros patenteiem o mesmo, e é o que dá citações e visibilidade.
4. Em qualquer caso: não publicar nada público (repositório, preprint, apresentação) antes de concluir os itens 1 e 2.

**O que o repositório deve conter, quando for aberto.** Código de geração por fórmula, decodificador em C, scripts de todos os benchmarks com sementes fixas, as matrizes exportadas, o relatório e um README que repita a tabela de posicionamento sem exagero. A credibilidade vem da reprodutibilidade e da franqueza sobre os limites.

## Apêndice: protocolo experimental e reprodutibilidade

Todos os experimentos usam Python 3 puro (mais numpy e openpyxl na geração) e um decodificador em C compilado com gcc -O3. As sementes são fixas em todos os scripts; os mesmos padrões de apagamento são aplicados a todos os códigos de uma comparação. O critério de sucesso é a recuperação integral de todos os símbolos, verificada por posto da submatriz apagada em GF(2).

| Script | O que faz | Entrada | Saída principal |
| --- | --- | --- | --- |
| pu3.py | Construção regular por fórmula (etapa 3) e busca de parâmetros | primo p | res_p.json |
| v5.py | Construção irregular com braços não transmitidos e cadeia fechada (etapa 4); comparação com 5G e PEG | primo p, v5_design.json | v5_p37.json, v5_p127.json |
| fair.py | Pré-código gaussiano com paridades perfuradas, em taxa idêntica (etapa 5) | v5_p*.json, tabelas 5G | falhas e peeling por fração de perda |
| gauss_dense.py | Equações densas gaussianas contra aleatórias | v5_p*.json | falhas por variante |
| floor.py | Piso de erro com amostras grandes e intervalo de Wilson | código e frações | floor_p_c.json |
| burst_eq.py | Rajadas com a mesma busca de ordem de envio para os três códigos | v5_p*.json | burst_eq_p.json |
| compare.py | Montagem do 5G NR (TS 38.212) e do PEG; decodificação por posto e por peeling | tabelas 5G_bg1.csv, 5G_bg2.csv | cmp_p.json |
| validate5g.py | Validação da montagem do 5G contra o codificador Sionna 2.2.0 | idem | matriz e codificação conferidas em seis casos |
| export_code.py, pudec.c | Exporta o código final e o decodifica em C com medição de tempo | fair.py | code_p37.txt, code_p127.txt, tempos |
| rq_bench.py, rq_time.py | Recuperação e tempo do RaptorQ (biblioteca raptorq 2.0.0) | k, n, tamanho de símbolo | taxas e tempos |

**Referências externas usadas.** Tabelas dos grafos-base do 5G NR e codificador de referência: pacote Sionna 2.2.0 (NVIDIA). RaptorQ: biblioteca raptorq 2.0.0 (implementação da RFC 6330 em Rust, com binding Python); os números de desempenho nativo citados são os publicados na página da biblioteca para um Ryzen 9 9950X3D com símbolos de 1.280 bytes.

**Máquina de medição.** Máquina virtual com Intel Xeon a 2,1 GHz, 2 vCPUs; XOR de pacotes de 1 KB a 11 GB/s, medido. Tempos absolutos variam com a máquina; as razões entre códigos medidos na mesma máquina são o que deve ser comparado.

**Tamanhos de amostra.** 1.480 símbolos: 150.000 a 400.000 padrões por condição nas medições de piso, 10.000 a 20.000 nas demais. 5.080 símbolos: 15.000 a 40.000 no piso, 300 a 2.000 nas demais. Rajadas: todos os 1.480 inícios no bloco pequeno, 150 a 300 inícios sorteados no grande. Tempo: 100 a 200 decodificações por condição.
