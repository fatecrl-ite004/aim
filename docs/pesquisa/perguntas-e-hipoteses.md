# Perguntas e hipóteses de pesquisa

**Estado:** questões de trabalho, não hipóteses confirmadas nem decisões técnicas.

## Pergunta principal

Em cenários definidos, a análise temporal conjunta de métricas de infraestrutura e API acrescenta capacidade de identificar eventos de degradação ou apoiar sua investigação, em comparação com baselines sob a mesma divisão temporal?

## Hipóteses a operacionalizar

- A combinação de métricas de infraestrutura e API pode acrescentar informação para detectar eventos definidos, relativamente à análise de métricas de API isoladas.
- A utilidade de limiares fixos ou variáveis depende do cenário e do critério de avaliação; não se presume vencedor universal.
- Métodos temporais/multivariados mais complexos só são úteis se superarem baselines em teste cronológico, sob medidas por evento e custo comparáveis.
- Sinais que precedem um evento podem apoiar avaliação de antecedência, desde que a janela e o horizonte sejam predefinidos; precedência não prova causalidade.

## Decisões necessárias antes de testar

Definir serviços/cenários, carga, falhas, métricas, unidade e rótulo de evento, período de antecedência, baselines, splits, métricas, tolerância event-wise e critérios de comparação. Também decidir se haverá dados reais, sintéticos, injetados ou combinação, observando licença e validade externa.

RCA, traces, topologia, adaptação online, retreinamento, similaridade vetorial e LLM permanecem questões opcionais. Sua inclusão requer pergunta própria, dados disponíveis, justificativa de custo e avaliação específica.
