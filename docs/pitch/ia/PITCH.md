# AIM — Active Infrastructure Monitor

## 1. O Problema

Em infraestruturas computacionais modernas, o monitoramento tradicional é essencialmente reativo. Thresholds estáticos só disparam quando os limites já foram ultrapassados — e o usuário final já experimenta indisponibilidade ou degradação de serviço.

A literatura científica documenta que thresholds estáticos geram excesso de falsos positivos em ambientes cloud dinâmicos, onde sazonalidade, picos de tráfego e mudanças arquiteturais tornam qualquer limite fixo inadequado. O resultado operacional são três problemas recorrentes: alta latência de detecção (MTTD elevado), fadiga de alertas causada por falsos positivos, e lentidão no diagnóstico de causa raiz (MTTR alto).

A pesquisa também aponta que anomalias em infraestrutura raramente se manifestam de forma isolada em uma única métrica. Frequentemente, a condição de risco só emerge quando múltiplas variáveis são analisadas em conjunto ao longo do tempo — o que a literatura chama de anomalias cross-variable. Tratá-las de forma univariada deixa esse padrão invisível.

## 2. A Solução

O AIM (Active Infrastructure Monitor) é uma proposta de observabilidade ativa que endereça diretamente o que a literatura identifica como lacuna central do campo: a análise multivariada conjunta de métricas de infraestrutura como séries temporais correlacionadas.

Utilizando o protocolo aberto OTLP (OpenTelemetry Protocol) para ingestão padronizada de métricas em tempo real, o AIM aplica modelos estatísticos e de aprendizado de máquina para:

1. **Correlacionar** como a degradação contínua da infraestrutura computacional (CPU, memória, IOPS, rede) se relaciona com a saúde de APIs e aplicações web (latência, throughput, taxas de erro HTTP).
2. **Detectar e prever anomalias temporais multivariadas** antes que culminem em falhas ou violação de SLAs, operando sobre o comportamento conjunto das métricas.
3. **Gerar diagnósticos contextualizados** via LLM/NLP que traduzem saídas numéricas em explicações interpretáveis para times de SRE, DevOps e Engenharia.

## 3. Principais Diferenciais

**Ingestão Padronizada via OTLP:** adoção do OpenTelemetry, framework vendor-neutral da CNCF, para coleta agnóstica de telemetria. Elimina dependência de ferramentas proprietárias e viabiliza correlação entre métricas de infraestrutura e de aplicação a partir de uma única fonte de dados.

**Análise Temporal Multivariada:** avaliação conjunta de múltiplos sinais interdependentes — CPU, RAM, IOPS e rede cruzados com latência, throughput e taxas de erro — em vez do tratamento por variável isolada, que a literatura aponta como insuficiente para detectar anomalias que emergem apenas nas relações entre variáveis.

**Scoring Dinâmico em vez de Thresholds Estáticos:** a pesquisa demonstra que funções de scoring dinâmicas — que adaptam sua referência de normalidade ao longo do tempo — superam funções estáticas na distinção entre oscilações benignas e desvios reais, com diferença estatisticamente significativa.

**Abordagem Preditiva e Ativa:** foco na antecipação do risco com base em padrões temporais históricos, não apenas na notificação pós-incidente. A previsão envolve incerteza — o AIM trabalha com estimativa de probabilidade de degradação, não com afirmações determinísticas sobre o futuro.

**Relatórios Contextualizados:** tradução das saídas dos modelos em diagnósticos interpretáveis para a equipe operacional, reduzindo o tempo de triagem e o requisito de especialização técnica aprofundada para identificação inicial do problema.

## 4. Onde Queremos Chegar

Demonstrar a viabilidade técnica de transformar a observabilidade de infraestruturas em uma camada preditiva ativa, com foco em reduzir o Tempo Médio de Detecção (MTTD) e simplificar o diagnóstico de causa raiz.

A avaliação será conduzida com métricas event-wise robustas — não com métricas point-adjusted, que a literatura demonstra inflar artificialmente o desempenho de qualquer detector, incluindo detectores aleatórios.

## 5. Princípio Central

O AIM não deve simplesmente detectar que um sistema está com problemas. Ele deve aprender o comportamento conjunto das métricas ao longo do tempo para identificar evidências de que o sistema pode estar caminhando para uma condição de degradação.

```
DETECÇÃO
"O problema já aconteceu."

versus

PREVISÃO
"Os dados indicam risco de que o problema aconteça."
```

A previsão envolve incerteza. O AIM trabalha com estimativa de risco e probabilidade — não com afirmações determinísticas sobre o futuro. O princípio central não é alertar quando um threshold é violado, mas aprender o comportamento temporal das métricas para identificar padrões que precedem a degradação.