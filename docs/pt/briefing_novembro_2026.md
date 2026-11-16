# **Briefing técnico — Prime-Ulam LDPC**

Evolução da arquitetura geométrica para reconstrução de bits apagados | Novembro de 2026

## **Resumo executivo**

Nosso projeto investiga uma nova família de códigos de correção de apagamentos baseada em **geometria de conexões, braços da Espiral de Ulam, pareamentos antípodas e ponderações radiais**.

O objetivo é desenvolver uma matriz de equações lineares capaz de reconstruir dados perdidos com eficiência comparável ou superior à dos códigos LDPC convencionais, preservando baixa redundância e complexidade computacional.

Até agora, os experimentos produziram três descobertas relevantes:

1. **A geometria importa para a construção da matriz**, mas não demonstramos que a geometria dos números primos seja intrinsecamente superior à aleatoriedade controlada.
2. **A intercalação antípoda com deslocamentos entre camadas** foi uma das construções mais competitivas, alcançando 94,93% de recuperação integral com 15% de apagamentos aleatórios em um dos experimentos.
3. **Restrições geométricas excessivamente rígidas podem destruir o desempenho**, como ocorreu quando exigimos a mesma distribuição de braços em todas as equações.

Nossa principal hipótese de pesquisa evoluiu. Não procuramos mais simplesmente reproduzir padrões dos primos: buscamos descobrir se **geometrias multiescalares podem organizar a independência das equações de forma mais eficiente do que construções convencionais**.

A evidência disponível ainda não permite afirmar superioridade sobre LDPCs modernos.

## **1. O desafio matemático**

O sistema utiliza a seguinte configuração experimental:

# **256**

Bits originais

# **64**

Bits de paridade

# **320**

Bits transmitidos

# **0,80**

Taxa do código

Construímos 64 equações XOR, cada uma envolvendo 16 bits de informação. Cada bit participa de quatro equações.

A matriz de verificação completa é:

\\[ H\_{\mathrm{full}}=[H\mid I\_{64}] \\]

Se um conjunto \\(E\\) de bits transmitidos for apagado, a recuperação integral é possível quando:

\\[ \boxed{\operatorname{rank}(H\_{\mathrm{full},E})=|E|} \\]

Nosso desafio consiste em construir \\(H\\) para maximizar a frequência dessa condição, especialmente quando as perdas ocorrem em rajadas.

**Uma distinção fundamental:** nossos testes mediram principalmente a recuperação integral dos 320 bits transmitidos, não apenas dos 256 bits originais. Recuperar somente os dados pode ser possível mesmo quando alguma paridade apagada permanece indeterminada.

Com 20% de apagamentos, perdemos 64 símbolos — exatamente o número de equações independentes disponíveis. Por isso, o sistema opera próximo ao limite algébrico e torna-se muito sensível a dependências entre colunas.

## **2. Evolução histórica das arquiteturas**

1. **Prime-Ulam original — Geometria dos números primos**

   As primeiras matrizes utilizavam alinhamentos associados às coordenadas dos primos na Espiral de Ulam: \\(x\\), \\(y\\), \\(x+y\\) e \\(x-y\\).

   A hipótese inicial era que a distribuição dos primos poderia fornecer uma organização natural das equações XOR. Os primeiros resultados foram competitivos com controles regulares aleatórios, sem demonstrar superioridade consistente.
2. **Interconexões entre braços**

   Passamos a conectar bits de setores angulares diferentes, procurando distribuir as dependências por regiões distantes.

   A construção interbraços melhorou a recuperação em rajadas de 15% em relação à diagonal, mas permaneceu abaixo do controle aleatório.
3. **Braços multigeométricos**

   Introduzimos braços fechados, intermediários, abertos e híbridos, sem exigir que todas as posições fossem números primos.

   A mistura de curvaturas superou as geometrias isoladas, mas algumas construções concentraram excessivamente as conexões e geraram muitos ciclos curtos.
4. **Antípodas e conexões intercaladas**

   Introduzimos a regra de conectar o primeiro bit de um braço ao último do braço oposto.

   A inversão fixa gerou dependências excessivas. A adição de deslocamentos entre camadas recuperou o desempenho e tornou a arquitetura competitiva.
5. **Ponderações radiais e função W**

   Investigamos pesos proporcionais a \\(R\\), \\(R^2\\), \\(R^{-1}\\), \\(\Delta R\\), \\(\Delta R^{-1}\\) e \\(\Delta R^{-2}\\), além de combinações de coeficientes.

   Os resultados indicaram diferenças entre ponderações, mas sem uma vantagem robusta e reproduzível.
6. **Antípoda invertida com restrições obrigatórias**

   Na geração mais recente, a imposição rígida de dois bits por braço em cada equação provocou forte aumento de ciclos curtos e queda acentuada da recuperação.

   Essa experiência identificou uma restrição de projeto que devemos abandonar, preservando apenas as propriedades geométricas úteis.

## **3. Os melhores resultados alcançados**

A tabela reúne os resultados mais relevantes relatados ao longo da pesquisa.

| Geração                                    | Recuperação aleatória, 15% | Recuperação em rajadas, 15% |
| ------------------------------------------ | -------------------------- | --------------------------- |
| Ulam diagonal original                     | 96,81%                     | 90,14%                      |
| Ulam interbraços                           | 96,25%                     | 92,50%                      |
| Multigeométrica híbrida                    | 71,00%                     | 32,20%                      |
| Antípoda otimizada                         | 97,22%                     | 93,61%                      |
| Mista otimizada                            | **97,83%**                 | 89,08%                      |
| Mista original                             | 96,92%                     | **93,25%**                  |
| Antípoda invertida intercalada             | 94,93%                     | 91,80%                      |
| Ponderação por ΔR                          | 96,08%                     | 87,75%                      |
| LDPC aleatório otimizado, geração antípoda | 96,94%                     | **95,14%**                  |

Valores de experimentos anteriores, com diferentes sementes, construções, amostras e procedimentos. A tabela documenta a evolução, mas não constitui um ranking estatístico entre todas as arquiteturas.

Marcos de recuperação em experimentos selecionados

Aleatórios

Rajadas

0%25%50%75%100%DiagonalInterbraçosAntípoda otim.Mista otim.LDPC otim.

Comparação histórica ilustrativa, não controlada entre gerações.

### **O que podemos concluir desses números?**

A arquitetura mista otimizada atingiu a maior taxa relatada entre as construções geométricas selecionadas para apagamentos aleatórios de 15%: 97,83%.

Nas rajadas, a antípoda otimizada atingiu 93,61%, mas o controle LDPC otimizado do mesmo experimento alcançou 95,14%.

O resultado mais instrutivo talvez seja o da antípoda invertida: a versão fixa recuperou apenas 4,13% dos casos com perdas aleatórias de 15%, enquanto a versão intercalada alcançou 94,93%. A alteração na organização dos pares produziu uma melhoria muito maior do que os ajustes posteriores de pesos.

Isso aponta para uma prioridade: **primeiro construir uma topologia sem dependências prejudiciais; depois otimizar a geometria e os coeficientes**.

## **4. Pipeline proposto para rivalizar com códigos clássicos**

1\. Dados e geometria

256 bits → posições na espiral → braços, ângulos e raios

2A. Local

Vizinhança e curvatura

2B. Intermediária

Conexões entre setores

2C. Antípoda

Inversão radial intercalada

3\. Construção da matriz H

64 × 256 | 16 conexões por linha | 4 por coluna

4\. Otimização algébrica e geométrica

Deficiência de posto + ciclos curtos + diversidade radial + fidelidade antípoda

5\. Codificação e transmissão

256 dados + 64 paridades XOR = 320 bits

6\. Canal com apagamentos

Perdas aleatórias, consecutivas e agrupadas

7\. Decodificação

Peeling → eliminação GF(2) → reconstrução dos bits

8\. Benchmark independente

Taxa de recuperação, latência, memória, ciclos e intervalos de confiança

O diferencial pretendido não está na operação XOR — que é convencional —, mas no **algoritmo que determina quais bits devem participar de cada equação**.

## **5. A evolução da função de otimização**

Nossa formulação radial mais recente é:

\\[ W\_{ij}= \alpha\Delta R+ \beta(\Delta R)^2+ \frac{\gamma}{\Delta R+\varepsilon}+ \frac{\delta}{(\Delta R+\varepsilon)^2} \\]

Entretanto, os testes mostraram que maximizar uma preferência geométrica isoladamente não garante boa recuperação.

Por isso, recomendo que a função objetivo principal seja:

\\[ \boxed{ J(H)= \lambda_D\mathbb E[D_E] +\lambda_C C_4(H) +\lambda_G G(H) } \\]

Onde:

- \\(D_E=|E|-\operatorname{rank}(H\_{\mathrm{full},E})\\) mede a deficiência de posto em padrões de apagamento.
- \\(C_4(H)\\) penaliza ciclos de comprimento quatro.
- \\(G(H)\\) penaliza desvios das propriedades geométricas desejadas, sem impor uma distribuição rígida por braço.

A função \\(W\\) deve servir como mecanismo para propor conexões, enquanto \\(J\\) decide quais propostas são realmente vantajosas.

Essa separação permite que a geometria participe da construção sem se sobrepor ao objetivo matemático de reconstrução.

## **6. Como competir com os códigos clássicos**

Até agora, utilizamos principalmente matrizes LDPC regulares aleatórias como controle. Isso é necessário, mas insuficiente para demonstrar competitividade com o estado da arte.

| Referência             | O que precisamos comparar                                           |
| ---------------------- | ------------------------------------------------------------------- |
| LDPC regular aleatório | Benefício da geometria frente à aleatoriedade                       |
| LDPC otimizado por PEG | Capacidade de evitar ciclos curtos                                  |
| QC-LDPC                | Regularidade estrutural, memória e eficiência                       |
| LDPC irregular         | Benefício de distribuições de graus não uniformes                   |
| Reed–Solomon           | Recuperação de apagamentos em símbolos, com redundância equivalente |
| Raptor/RaptorQ         | Eficiência e recuperação em canais de apagamento                    |

As comparações deverão utilizar taxa de código, tamanho de bloco, modelo de canal e critérios de sucesso equivalentes.

Não basta superar uma matriz aleatória. Para rivalizar com códigos modernos, precisaremos demonstrar vantagens em **taxa de recuperação, custo computacional ou robustez a rajadas**.

## **7. Melhorias prioritárias**

**Prioridade 1 — Antípoda intercalada flexível**

Preservar o pareamento radial invertido, mas permitir que a quantidade de pares antípodas varie entre equações. Evitar repetições entre camadas.

**Prioridade 2 — Otimização direta do posto**

Usar conjuntos de apagamentos durante o treinamento e minimizar a deficiência média das submatrizes. Reservar outros conjuntos para validação independente.

**Prioridade 3 — Otimizar W e a proporção antípoda**

Buscar conjuntamente \\(\alpha,\beta,\gamma,\delta\\), a regularização \\(\varepsilon\\), os deslocamentos entre camadas e a fração de conexões opostas.

**Prioridade 4 — Otimizar a disposição dos bits transmitidos**

A resistência a rajadas depende também da ordem dos 320 bits no canal. Devemos comparar layouts originais, embaralhados e intercalados, sem confundir melhorias de posicionamento com melhorias do código.

**Prioridade 5 — Benchmark estatístico rigoroso**

Utilizar pelo menos 20 matrizes independentes na próxima etapa, milhares de padrões de apagamento por condição e intervalos de confiança. Aumentar as amostras conforme a variabilidade observada.

## **8. Roadmap de desenvolvimento**

| Fase                | Entrega                        | Critério de avanço                                   |
| ------------------- | ------------------------------ | ---------------------------------------------------- |
| I — Construção      | Gerador antípoda flexível      | Regularidade exata e ausência de conexões duplicadas |
| II — Otimização     | Busca de W e deslocamentos     | Redução da deficiência de posto em validação         |
| III — Decodificação | Peeling + GF(2)                | Recuperação correta e medição de latência            |
| IV — Benchmark      | Comparação com LDPC otimizado  | Ganhos reproduzíveis em condições equivalentes       |
| V — Escalabilidade  | Blocos de 1.024 e 4.096 bits   | Desempenho e custo computacional sustentáveis        |
| VI — Publicação     | Código, dados e artigo técnico | Resultados integralmente reproduzíveis               |

## **9. A decisão estratégica**

Nossa trajetória revelou uma mudança importante de abordagem.

**Concepção inicial:** encontrar uma vantagem na distribuição dos números primos.

**Evolução:** explorar a geometria da espiral e a diversidade de braços.

**Concepção atual:** projetar matrizes esparsas por meio de conexões antípodas intercaladas, ponderações radiais e otimização algébrica.

A hipótese científica central pode ser expressa assim:

> Uma topologia esparsa que combina conexões locais, intermediárias e antípodas radialmente intercaladas pode reduzir dependências prejudiciais entre equações e aumentar a capacidade de reconstrução de dados, em comparação com códigos de mesma redundância e complexidade.

Essa é uma hipótese testável, não uma conclusão já demonstrada.

**Minha recomendação é concentrar a próxima fase em uma única arquitetura candidata: PAI-W Flexível**, combinando antípodas invertidas, deslocamentos variáveis, distribuição não uniforme de braços e otimização direta da deficiência de posto.

Se essa arquitetura superar consistentemente um LDPC otimizado sob o mesmo protocolo, teremos um resultado científico substancial. Se não superar, ainda poderemos identificar quais propriedades geométricas são úteis e quais introduzem redundâncias algébricas indesejadas.

O objetivo deixa de ser provar que a Espiral de Ulam é superior e passa a ser **descobrir se uma geometria estruturada e otimizada consegue oferecer vantagens mensuráveis sobre os códigos clássicos**.

Nota metodológica: este briefing consolida os resultados relatados nas etapas anteriores da conversa. Não constitui uma auditoria independente dos arquivos de ensaio ou dos códigos de simulação. Antes de uma publicação científica, será necessário reproduzir os benchmarks a partir das matrizes, sementes, algoritmos e dados brutos.