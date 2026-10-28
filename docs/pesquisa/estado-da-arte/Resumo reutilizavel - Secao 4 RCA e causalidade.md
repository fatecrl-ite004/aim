# Seção 4 — Análise de causa raiz em microsserviços

## Escopo

Quatro artigos: survey de detecção/RCA, avaliação de inferência causal e dois sistemas de diagnóstico por traces/grafos. Fluxo conceitual: detectar sintoma, limitar serviços/métricas afetadas e ranquear causas prováveis. Correlação não é, sozinha, prova de causalidade.

## 1. Soldani e Brogi (2021) — *Anomaly Detection and Failure Root Cause Analysis in (Micro)Service-Based Cloud Applications: A Survey*

**Área/objetivo.** Survey de detecção de sintomas de falha e explicação de causas em aplicações cloud/microsserviços. Diferencia falha (incapacidade de cumprir função) de anomalia observável (latência, throughput, erros ou logs inesperados).

**Método.** Revisão qualitativa organizada por fonte de observabilidade: logs, distributed tracing e monitoramento. Para RCA, categoriza técnica, integração com detecção, tipo/granularidade da anomalia, causa identificada e entradas requeridas. Inclui correlação, grafos de dependência/causalidade, random walk e comparação de traces.

**Como reutilizar.** Escolher a técnica conforme sinais disponíveis e tipo de falha; alinhar granularidade do detector e do diagnóstico; listar requisitos de instrumentação, topologia e histórico. Avaliar detecção e localização separadamente, com falsos positivos/negativos e custo.

**Limite/conclusão.** Não há solução universal: técnicas exigem artefatos distintos, muitos trabalhos cobrem cenários limitados e a integração entre detecção e RCA varia. Survey não apresenta experimento próprio nem ranking homogêneo; literatura levantada até 2021.

## 2. Wu et al. (2021) — *Causal Inference Techniques for Microservice Performance Diagnosis: Evaluation and Guiding Recommendations*

**Pergunta/métodos.** Compara GC, PC com teste de correlação, PC com kernel, GES, CAM e LiNGAM para cenários de muitos sinais, sintomas heterogêneos e diferentes causas. Usa Sock Shop (13 serviços) e Train Ticket (41), injeta latência (200 ms), CPU hog e memory leak, com carga ~450–600 consultas/s e Prometheus a cada 5 s via Istio/cAdvisor/node-exporter. Aprende grafo causal e ranqueia com PageRank; avalia PR@k/AP; compara redução BIRCH e baseline de dependência conhecida.

**Resultados.** Sem seleção de features, serviço culpado teve PR@1 até 27% no resumo coarse-grained. Seleção de métricas anômalas elevou PR@3 em média 77,4%. Na localização fina, sem filtragem, médias de PR@1=5,6% e PR@5=20,6%; filtragem aumentou PR@5 em média 29,1%. GC foi melhor em latência; diversos métodos em CPU hog; LiNGAM foi competitivo em localização fina após filtragem. PC-kernel e GES escalam em custo com número de métricas; num cenário a correlação mais topologia conhecida superou CI.

**Recomendação e reprodução.** Integrar detector/score para separar relações normais de relações anômalas; localizar primeiro serviço, depois métrica; adaptar método ao sintoma. Reproduzir injeções, frequência de coleta, parâmetros, topologia e métricas PR@1/3, AP@5; executar com/sem redução de features e reportar custo.

**Limites.** Duas aplicações, falhas selecionadas e testbed de laboratório. Cada método assume condições diferentes (linearidade/gaussianidade); nenhum vence em todos os cenários. Ground truth é derivado das injeções.

## 3. Gan et al. — *Sleuth: A Trace-Based Root Cause Analysis System for Large-Scale Microservices with Graph Neural Networks*

**Problema/método.** RCA não supervisionada em traces, onde spans e chamadas formam grafos e sintomas se propagam. Sleuth usa GNN, agregação GIN para modelar estado/propagação, distância entre traces e clustering de traces anômalos para reduzir inferência. Também oferece gerador sintético configurável; instrumenta com OpenTelemetry, Prometheus e Kubernetes. Treina sem labels e usa logs de falhas injetadas como verdade de referência na avaliação.

**Avaliação/resultados.** Usa SockShop, SocialNetwork (DeathStarBench) e serviços sintéticos até 1024 componentes em cluster K8s de 100 nós; compara TraceAnomaly, Realtime RCA, Sage, GCN/GIN e DeepTraLog. Sleuth-GIN sem clustering reporta F1 de 0,86–0,94 e acurácia 0,84–0,92 nas tabelas de diferentes escalas. Ao escalar Syn-16 para Syn-1024, treino/inferência aumentam ~3,3×/16,3×, contra 39,5×/33,9× para Sage. Também demonstra ajuste few-shot para aplicação nova.

**Como replicar.** Recriar benchmarks/versões e carga; instrumentar parent spans; injetar CPU, rede, memória e disco em container/pod/nó; usar registros de injeção como labels; treinar, comparar variantes de clustering e medir F1/acurácia/tempo. Testar mudança de topologia e transferência.

**Limites.** Parte substancial usa geração sintética e injeção aleatória; isso não reproduz toda variedade de incidentes reais. Desempenho de benchmark não demonstra por si só redução de MTTR.

## 4. Ding et al. (2023) — *TraceDiag: Adaptive, Interpretable, and Efficient Root Cause Analysis on Large-Scale Microservice Systems*

**Problema/método.** Reduzir custo de RCA em traces com centenas de componentes, podando redundâncias sem apagar a causa. Usa reinforcement learning para aprender árvore/política de poda; Transformer escolhe ações; recompensa combina simplicidade do grafo e qualidade diagnóstica. Sobre o grafo reduzido aplica método causal com modelos bayesianos por componente e valores de Shapley para atribuir mudança da latência frontend entre janela normal e janela de alerta.

**Dados/resultados.** Usa traces de produção do Microsoft Exchange. Na tabela de nove casos, PR@1=0,667, PR@3=0,852, PR@5=0,956, PR@Avg=0,834 e RankScore=0,818, superando BackTrace e GrootRank. Para uso online, usa um dia de dados do incidente e sete dias anteriores como base; total de incidentes não divulgado. Reporta ganho de 75,1% em PR@Avg contra heurística e redução do tempo de diagnóstico de 50% em casos fáceis e >96,5% nos difíceis.

**Como replicar/testar.** Paper não fornece dados corporativos. Em sistema próprio, coletar traces rotulados e topologia; separar incidentes por caso/tempo; aprender poda sem rótulos do teste; comparar poda aleatória, heurística e RL; medir PR@k, RankScore, nós removidos, tempo e frequência com que a raiz foi podada; revisar explicações com operadores.

**Limites.** Resultados de produção são relevantes, mas dados e quantidade de incidentes não são públicos, impedindo reprodução exata. Dependência de labels especializados e da estrutura do Exchange limita transferência automática.

## Síntese reutilizável

Pipeline recomendada: detectar sintoma; filtrar sinais/serviços afetados; usar topologia e traces para gerar candidatos; ranquear causas; retornar evidências interpretáveis; validar com operador. Avalie por incidentes não vistos, reporte PR@k e custo/tempo, injete falhas diversas e verifique se filtragem/poda preserva a causa. Métricas, traces e inferência causal são complementares e precisam de ground truth.

## Fontes consultadas

`state_of_art/seção 4`: `Anomaly Detection and Failure Root Cause Analysis in (Micro) Service Based Cloud Applications A Survey.pdf`; `Causal Inference Techniques for Microservice Performance Diagnosis Evaluation and Guiding Recommendations.pdf`; `Sleuth A Trace Based Root Cause Analysis System for Large Scale Microservices with Graph Neural Networks.pdf`; `TraceDiag Adaptive, Interpretable, and Efficient Root Cause Analysis on Large Scale Microservice Systems.pdf`.
