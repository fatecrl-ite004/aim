# Visão e escopo

**Revisado em:** 28 de outubro de 2026.

AIM significa **Active Intelligent Monitoring**. O título do TCC é *AIM: Uma análise multivariada de anomalias temporais em infraestruturas computacionais*. A pesquisa aplicada propõe uma prova de conceito para coletar métricas de infraestrutura e APIs por OTLP, analisar séries temporais multivariadas e apresentar evidências em aplicação web com visualizações, indicadores de saúde e RBAC.

O objetivo é avaliar se a análise conjunta e temporal ajuda a identificar degradações e a apoiar a investigação humana. Eventual antecipação de eventos, redução de alertas e melhoria operacional dependem de hipóteses, cenários, rótulos e avaliação; não são resultados existentes.

## Incluído na direção de pesquisa

- Métricas de infraestrutura, como CPU, memória, I/O e rede, e de API, como latência, throughput e erros, conforme instrumentação disponível.
- Transporte de métricas por OTLP, preservação de timestamps e análise em janelas temporais.
- Comparação de baselines simples e métodos estatísticos ou de aprendizado de máquina.
- Aplicação web com representação de séries, eventos e contexto, além de controle de acesso por perfil (RBAC).
- Avaliação de detecção, e de risco antecipado apenas se houver definição de evento e horizonte.

## Fora do escopo atual

O AIM não executa remediação automática, mudanças em código, commits, pull requests ou deploys. A decisão continua com pessoas. LLM, traces, logs, topologia e RCA avançada são possibilidades condicionais, não componentes obrigatórios ou garantidos.

## Limites conceituais

Detecção de anomalia, forecasting de valores, previsão de risco de evento, detecção de change point e RCA têm alvos distintos e requerem critérios próprios. Limites fixos e variáveis são alternativas a avaliar por cenário. Correlação ou precedência temporal indica associação observada e não comprova causalidade.

Componentes de software, banco de dados, framework, forma de implantação, frequência de coleta, retenção, modelo final e limiar final permanecem em aberto. A arquitetura em [visão geral](../arquitetura/visao-geral.md) é conceitual.
