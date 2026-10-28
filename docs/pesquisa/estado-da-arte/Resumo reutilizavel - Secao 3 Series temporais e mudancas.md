# Seção 3 — Séries temporais, mudanças e detecção multivariada

## Escopo

A seção cobre detecção de change points, limiar adaptativo e dois detectores profundos de séries multivariadas. `Anomaly Detection A Survey.pdf` também aparece na seção 2; foi resumido lá e não tratado como novo paper nesta seção.

## 1. Aminikhanghahi e Cook (2017) — *A Survey of Methods for Time Series Change Point Detection*

**Área/problema.** Detectar instantes em que muda a distribuição ou o estado gerador de uma série. Um change point pode iniciar um novo regime normal, portanto não é sinônimo de outlier.

**Metodologia.** Survey de métodos supervisionados e não supervisionados; compara custo, dimensionalidade, limitações, desempenho e operação online/offline. Abrange classificação, razões de verossimilhança/densidade, subespaço, Bayesian online change point detection, Gaussian Processes, clustering e MDL. Discute métricas de classificação e erro temporal.

**Conclusões.** Supervisionados tendem a ser mais precisos quando há dados suficientes e estacionários; não supervisionados são úteis quando isso não vale. RuLSIF tem bons resultados publicados, porém sem benchmark uniforme abrangente. Latência, tamanho da janela, dimensionalidade, threshold e não estacionariedade são trade-offs. Os autores apontam necessidade de avaliação de robustez, janela variável e métricas de atraso.

**Como testar.** Usar séries anotadas ou mudanças injetadas; separar experimento online/offline; medir precisão/recall/F1 e erro temporal/atraso; variar ruído, dimensão e janela; reportar custo e alertas falsos por tempo.

**Limite.** Survey de 2017, sem experimento próprio; resultados vêm de estudos com datasets e protocolos diferentes e não são diretamente comparáveis.

## 2. Sivaraman (2022) — *Adaptive Thresholding in ML-Driven Alerting Systems for Reducing False Positives in Production Environments*

**Área/proposta.** Alertas para métricas de produção com sazonalidade e variações legítimas que tornam limites fixos ruidosos. Combina previsão LSTM, erro de reconstrução de autoencoder e contexto (horário/dia); cita clustering como k-means para adaptar limiares por padrão.

**Evidência declarada.** Descreve casos de uso, inclusive tráfego sintético de e-commerce, e relata ~40% de redução de falsos positivos num teste controlado de um mês. Não documenta dados, número de séries, split, parâmetros, algoritmo de limiar, definição de FP ou incerteza; não há protocolo suficiente para reproduzir esse número.

**Como tornar testável.** Especificar o limiar (por exemplo, previsão condicional mais quantil do erro residual calculado só no treino); comparar com threshold fixo e média móvel; fazer split temporal; manter teste intocado; medir falsos alertas/dia, recall, atraso e deriva. Simular sazonalidade legítima e injetar falhas para verificar se adaptação não as mascara.

**Limite/uso.** Tratar 40% como resultado reportado, não como evidência independente. A proposta é hipótese de desenho que precisa de especificação e validação próprias.

## 3. He et al. (2020/2021) — *A Spatiotemporal Deep Learning Approach for Unsupervised Anomaly Detection in Cloud Systems* (TopoMAD)

**Problema.** Métricas de nuvem são dependentes no tempo e conectadas por topologia; concatenação simples perde relações e treino não supervisionado pode conter anomalias.

**Método.** Representa componentes como nós e interações como arestas, usa janelas de métricas, extrai dependência espacial por GCN ou GAT e dependência temporal por LSTM dentro de um VAE seq2seq estocástico. O score é baseado na probabilidade/reconstrução. Propõe seleção de threshold não supervisionada e avalia robustez à contaminação. Publica dois datasets: MBD (batch/big data) e MMS (microserviços), com falhas injetadas.

**Avaliação/achados.** Compara métodos estatísticos, de vizinhança e redes neurais; usa AP/mAP, ROC e ablações da topologia/VAE. A topologia ajuda, embora grafo imperfeito não elimine totalmente o desempenho. Baselines mudam de posição entre MBD e MMS; há sensibilidade à severidade, contaminação e inicialização. Analisa complexidade e escala por topologias sintéticas maiores.

**Como reproduzir.** Usar código e datasets referidos no artigo; construir grafo; alinhar e normalizar métricas; criar janelas; treinar com possíveis anomalias; comparar GCN/GAT, sem topologia e sem VAE; selecionar limiar sem labels de teste; repetir seeds; reportar AP, ROC, eventos, FPs e custo.

**Limites.** Topologia pode ser dinâmica/incompleta; a evidência cobre dois contextos e injeções específicas. Os resultados variam com dados e inicialização.

## 4. Su et al. (2021) — *Multivariate Time Series Anomaly Detection and Interpretation Using Hierarchical Inter-Metric and Temporal Embedding* (InterFusion)

**Problema/método.** Detectar anomalias e indicar dimensões explicativas em séries multivariadas. Usa VAE hierárquico com duas variáveis latentes para embedding intermetric e temporal, two-view embedding e prefiltering para reduzir sobreajuste a anomalias no treino. Para interpretação, propõe imputação MCMC e métrica aproximada voltada a avaliação por operadores.

**Dados/resultados.** Avalia SWaT, WADI, SMD (12 entidades sem drift selecionadas) e ASD. ASD tem 12 servidores, 19 métricas, 45 dias em intervalos de 5 min; 30 dias para treino e 15 para teste. Reporta AUROC médio 0,9904, AP 0,9582 e aF1 total 0,957 no ASD, superando baselines tabuladas. Parte das métricas utiliza point-adjust e threshold ótimo, portanto não corresponde a operação prospectiva com threshold congelado.

**Como replicar.** Usar repositório/dados indicados; manter split temporal; configurar janela W=100 em SMD/ASD e W=30 em SWaT/WADI; seguir pretraining VAE temporal, early stopping e parâmetros publicados; comparar baselines; repetir seeds; calcular AUROC/AP e métricas eventuais sem point-adjust; testar contaminação e drift. Avaliar dimensões explicadas contra labels e especialistas.

**Limites.** Threshold ótimo/point-adjust pode elevar resultados retrospectivos; transferência para outra telemetria requer nova validação. A reprodução do ASD depende de disponibilidade do repositório.

## Síntese reutilizável

Change point detecta troca de regime; anomaly scoring marca padrões improváveis; threshold adaptativo muda o critério conforme contexto. Defina qual problema resolve, separe treino/validação/teste no tempo, compare baselines, reporte atraso e falsos alertas e teste drift/contaminação.

## Fontes consultadas

`state_of_art/seção 3`: `A Survey of Methods for Time Series Change Point Detection.pdf`; `Adaptive-Thresholding-in-ML-Driven-Alerting-Systems-for-Reducing-False-Positives-in-Production-Environment1.pdf`; `A Spatiotemporal Deep Learning Approach for Unsupervised Anomaly Detection in Cloud Systems...pdf`; `Multivariate Time Series Anomaly Detection and Interpretation Using Hierarchical Inter-Metric and Temporal Embedding.pdf`. O survey duplicado da seção 2 não foi recontado.
