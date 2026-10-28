# Seção 2 — Detecção de anomalias em séries temporais

## Escopo

Cinco artigos: survey geral, avaliação comparativa multivariada, estudo industrial, método SVDD e benchmark de métodos profundos. A síntese cobre área, método, achados, reprodução e limites.

## 1. Chandola, Banerjee e Kumar (2009) — *Anomaly Detection: A Survey*

**Área/problema.** Identificar observações ou padrões que não seguem o comportamento esperado em dados tabulares, sequenciais e relacionais, reconhecendo que anomalia depende do contexto e dos rótulos disponíveis.

**Método.** Survey e taxonomia, sem experimento próprio. Distingue anomalias pontuais, contextuais e coletivas; organiza técnicas em classificação, vizinhança, clustering, estatística, teoria da informação e métodos espectrais. Discute cenários supervisionados, semissupervisionados e não supervisionados.

**Uso/teste.** Definir unidade (ponto, janela, evento ou entidade), contexto e hipótese de normalidade; comparar com baseline estatístico; avaliar precisão, recall, F1 e custo; analisar falsos positivos por regime. A taxonomia orienta escolha, não fornece um único pipeline.

**Limite.** Survey de 2009; útil conceitualmente, mas não cobre a literatura recente.

## 2. Garg et al. (2021) — *An Evaluation of Anomaly Detection and Diagnosis in Multivariate Time Series*

**Área/pergunta.** Avalia estabilidade da comparação de detectores multivariados e funções de scoring em benchmarks.

**Método.** Dez detectores e quatro funções de score em sete datasets e 114 entidades; cinco sementes; testes de Friedman e pós-teste de Hochberg. Propõe FC1, combinação de precisão pontual e recall de eventos para reduzir distorções de métricas tradicionais em anomalias longas.

**Achados.** A função de score muda significativamente o ranking. Gauss-D e Gauss-D-K dinâmicos superam opções estáticas em diversos cenários; um autoencoder simples por canal (UAE) fica entre os melhores em ranking médio. A avaliação é parte central do resultado, não detalhe secundário.

**Reprodução/teste.** Reexecutar datasets e protocolos, fixar seeds, cruzar modelo e score, reportar medidas por ponto e evento e aplicar comparações estatísticas corrigidas. Em aplicação real, separar validação e teste cronologicamente e não selecionar limiar com labels de teste.

**Limites.** Predomínio de anomalias temporais e poucos conjuntos confiáveis para anomalias entre métricas. “Best F” e top-k podem usar informação de labels/eventos que não existe em produção.

## 3. Islam et al. (2021) — *Anomaly Detection in a Large-Scale Cloud Platform*

**Área/problema.** Detectar anomalias em tráfego/serviço cloud com sazonalidade e rótulos incompletos.

**Solução.** Sistema de streaming industrial com autoencoder GRU. Agrega telemetria HTTP a cada cinco minutos; agrupa por endpoint, método e status, acrescenta estatísticas/sazonalidade e converte erro de reconstrução em likelihood/score por janela móvel. Descreve cerca de 9000 pontos iniciais (~um mês), atualização online, retreino em lote a cada seis horas e feedback de operadores via Slack.

**Resultados.** Em conjunto de uma VM com 265.200 linhas, F1=0,8489 e precisão=0,7374. Reporta nenhum falso negativo segundo feedback dos operadores; um caso de produção teria sido detectado cerca de 20 minutos antes, evidência operacional não controlada.

**Como testar.** Replicar agregação, GRU autoencoder, janela e score; preservar ordem temporal; selecionar limiar apenas no treino/validação; simular fluxo e atualização; comparar com regra estática e modelo sem sazonalidade. Medir precisão, recall, alertas/dia, atraso e estabilidade sob drift; separar feedback humano de rótulo auditado.

**Limites.** Dados brutos multidimensionais e configurações completas não estão disponíveis no artigo consultado. Uma VM e feedback operacional não permitem generalização direta.

## 4. Huang et al. (2017) — *Time Series Anomaly Detection for Trustworthy Services*

**Método.** RLPSVDD: Support Vector Data Description relaxado por programação linear e pesos de densidade. Usa embedding temporal com atraso e janelas deslizantes com saltos; distância/violação da fronteira gera score de anomalia.

**Avaliação/reprodução.** Compara em séries Yahoo A1 (67 séries) e coleções associadas a Twitter, Etsy e Numenta. Registrar normalização, janela, atraso, parâmetros e limiar; reportar precisão, recall e F1 por série e agregado.

**Limite importante.** A seleção de parâmetros minimiza FP+FN com rótulos da própria série. Isso é seleção retrospectiva com rótulos, não avaliação totalmente não supervisionada/prospectiva. Ao replicar, reservar validação separada e teste cronológico bloqueado.

## 5. Wagner et al. (2023) — *TimeSeAD: Benchmarking Deep Multivariate Time-Series Anomaly Detection*

**Área/método.** Toolkit e benchmark para avaliar detectores profundos multivariados e auditar problemas em datasets/métricas. Compara 28 métodos em 21 conjuntos (15 subconjuntos SMD e seis Exathlon após filtragens descritas), identifica vieses como posição de anomalias, janelas longas e mudança de distribuição, e propõe TRec/TPrec e F1 sensível a eventos.

**Achados/uso.** Não há vencedor universal; métodos anteriores continuam competitivos. Reproduzir implementação, splits e seeds; reportar desempenho por dataset, evento e custo; manter holdout futuro bloqueado para evitar escolha de modelo pelo teste.

**Limites.** Ranking depende dos datasets, filtros, definição de evento e hiperparâmetros. Resultado de benchmark não garante transferência para telemetria de outra aplicação.

## Síntese reutilizável

Defina o evento-alvo; preserve cronologia; evite vazamento; inclua baseline; compare scores e limiares; reporte métricas pontuais e eventuais; repita seeds; meça custo e atraso; analise por entidade e tipo de anomalia. Não interprete o melhor F1 retrospectivo como promessa de produção.

## Fontes consultadas

`state_of_art/seção 2`: `Anomaly Detection A Survey.pdf`; `An Evaluation of Anomaly Detection and Diagnosis in Multivariate Time Series.pdf`; `Anomaly Detection in a Large-Scale Cloud Platform.pdf`; `Time Series Anomaly Detection for Trustworthy Services.pdf`; `TimeSeAD Benchmarking Deep Multivariate Time-Series Anomaly Detection.pdf`.
