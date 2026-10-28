# Glossário do projeto

| Termo | Uso neste repositório |
| --- | --- |
| AIM | Active Intelligent Monitoring, projeto de pesquisa e PoC. |
| OTLP | Protocolo OpenTelemetry para transporte de telemetria; não é detector nem método analítico. |
| Métrica | Medida numérica associada a uma entidade e a um instante ou intervalo de coleta. |
| Série temporal | Sequência de observações ordenadas temporalmente. |
| Anomalia | Observação, janela ou evento que se desvia de uma referência definida; a unidade e o contexto dependem do experimento. |
| Forecasting | Estimativa de valores futuros de uma série; não equivale automaticamente a previsão de incidente. |
| Risco | Estimativa relativa a um evento-alvo e horizonte explicitamente definidos. |
| Change point | Instante ou região em que o regime gerador dos dados muda; a mudança pode corresponder a novo regime normal. |
| Threshold / limiar | Regra de decisão aplicada a uma métrica ou score. Pode ser estática ou contextual; a escolha é experimental. |
| Event-wise | Avaliação por evento rotulado, com regra de correspondência, tolerância e atraso explicitados. |
| Leakage / vazamento | Uso indevido entre treino, validação e teste de informação que não estaria disponível no momento da previsão, como compartilhar observações-alvo ou ajustar transformações com o teste. |
| Correlação temporal | Associação entre sinais ao longo do tempo; isoladamente não estabelece direção causal. |
| RCA | Root Cause Analysis; processo de ranquear ou investigar causas candidatas sob dados e hipóteses definidos. |
| RBAC | Controle de acesso baseado em papéis. A aplicação web é proposta; detalhes de perfis estão em aberto. |
| PoC | Prova de conceito usada para avaliar viabilidade em cenários delimitados. |
| SRE | Site Reliability Engineering / Engineer, conforme contexto. |
| SOC Lead | Neste projeto, liderança de suporte operacional e triagem de eventos de produto; não implica escopo de cibersegurança. |
| LLM | Modelo de linguagem. Se investigado, deve ser complementar à apresentação de evidências, não motor decisor. |
