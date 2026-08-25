# AIM — Discovery de fundamentação: normas, SRE e pesquisa acadêmica

## Objetivo

Este documento organiza uma primeira pesquisa de *discovery* para fundamentar academicamente o AIM, com foco em:

- escolha e justificativa das métricas observadas;
- definição de qualidade, confiabilidade e desempenho;
- definição de eventos/targets de previsão;
- previsão de degradação e indisponibilidade;
- análise de séries temporais e métricas correlacionadas;
- avaliação de modelos e riscos de falsos positivos/falsos negativos.

O pitch atual define o AIM como uma camada de observabilidade que monitora, mede, analisa, estima risco e notifica, sem intervenção automática nesta fase. [Fonte: pitch AIM, linhas 24–44 e 83–93.]

---

# 1. Base normativa

## 1.1 ISO/IEC 25010:2023 — Product Quality Model

**Fonte oficial:** https://www.iso.org/standard/78176.html

A ISO/IEC 25010:2023 define um modelo de qualidade aplicável a produtos de software e TIC. O modelo possui características e subcaracterísticas relacionadas a propriedades de qualidade e pode ser utilizado como referência para especificar, medir e avaliar qualidade.

### Relevância para o AIM

É uma das principais normas para justificar a pergunta:

> Por que determinadas propriedades do sistema devem ser medidas?

A norma não determina quais features de ML devem ser usadas nem qual deve ser o horizonte de previsão. Seu papel é fornecer uma referência para **qualidade e medição**.

### Uso proposto

**ISO/IEC 25010 → propriedades de qualidade → características observáveis → métricas**

Isso pode fundamentar a camada conceitual antes da escolha empírica das features.

**Fonte:** ISO, ISO/IEC 25010:2023.

---

## 1.2 ISO/IEC 20000-1:2018 — Service Management

**Fonte oficial:** https://www.iso.org/standard/70636.html

A ISO/IEC 20000-1:2018 especifica requisitos para estabelecer, implementar, manter e melhorar continuamente um sistema de gestão de serviços. A norma também contempla monitoramento, medição e revisão do sistema e dos serviços.

### Relevância para o AIM

É especialmente útil para fundamentar o contexto de:

- gestão de serviços;
- monitoramento;
- medição;
- avaliação;
- melhoria contínua.

Isso se conecta diretamente ao fluxo atual:

```text
Monitorar
   ↓
Medir
   ↓
Analisar
   ↓
Prever risco
   ↓
Notificar
```

### Limitação

Não deve ser utilizada para afirmar que uma métrica específica, como CPU ou RAM, é necessariamente preditiva de uma falha. A norma sustenta o contexto de **gestão e medição de serviços**, não o desenho do modelo de ML.

**Fonte:** ISO, ISO/IEC 20000-1:2018.

---

# 2. Base técnica — SRE, SLI e SLO

## 2.1 Google SRE — Service Level Objectives

**Fonte:** https://sre.google/sre-book/service-level-objectives/

O material do Google SRE define SLI como uma medida quantitativa de algum aspecto do nível de serviço.

Entre os exemplos apresentados estão:

- request latency;
- error rate;
- throughput;
- availability.

O material também recomenda definir claramente janela de medição, frequência de coleta, população observada e método de agregação.

### Relevância para o AIM

Esta é uma das bases técnicas mais diretamente relacionadas às métricas da API.

O AIM atualmente considera:

```text
API
├── Latência
├── Erros HTTP
├── Requests/s
├── Timeouts
└── Disponibilidade
```

A literatura SRE fornece fundamento técnico para a utilização de latência, erros, throughput e disponibilidade como indicadores do comportamento de um serviço.

### Ponto importante

O SRE também alerta que não devemos simplesmente coletar todas as métricas disponíveis. Devemos selecionar indicadores representativos da saúde do serviço.

Isso reforça a estratégia atual do AIM de coletar inicialmente e investigar posteriormente quais sinais realmente possuem valor preditivo.

---

## 2.2 Google SRE — The Four Golden Signals

**Fonte:** https://sre.google/sre-book/monitoring-distributed-systems/

Os quatro Golden Signals são:

1. **Latency**
2. **Traffic**
3. **Errors**
4. **Saturation**

### Relação com o AIM

Existe uma correspondência bastante direta:

| Golden Signal | AIM |
|---|---|
| Latency | Latência |
| Traffic | Requests/s / throughput |
| Errors | Erros HTTP |
| Saturation | CPU, memória, recursos e outros indicadores de saturação |

Isso fornece uma base técnica muito forte para a seleção inicial das métricas da API e do servidor.

---

# 3. Base técnica — confiabilidade e indicadores de risco

## 3.1 Google SRE — Measuring Reliability

**Fonte:** https://sre.google/resources/practices-and-processes/measuring-reliability/

O material diferencia indicadores relacionados ao que já aconteceu de indicadores que podem fornecer informação sobre o estado de risco atual do sistema.

Um exemplo apresentado é um sistema com 99% de utilização de disco: o sistema ainda funciona, mas a condição pode indicar risco futuro.

### Relevância

Isso é conceitualmente próximo da distinção central do AIM:

```text
Detecção
"O problema já aconteceu."

versus

Previsão
"Os dados indicam risco de que o problema aconteça."
```

Portanto, a literatura SRE ajuda a sustentar a ideia de que o AIM não deve ser apenas um detector de threshold.

---

# 4. Base acadêmica — observabilidade, anomalias e microserviços

## 4.1 Survey: Anomaly detection and root-cause identification in microservices

**2026 — Cluster Computing / Springer**

**Fonte:** https://link.springer.com/article/10.1007/s10586-026-06095-9

Este survey revisa 117 estudos publicados entre 2012 e 2025 sobre detecção de anomalias e identificação de causa-raiz em microserviços.

### Achados relevantes para o AIM

O trabalho discute:

- métricas de latência;
- tempo de resposta;
- throughput;
- CPU;
- memória;
- tráfego de rede;
- I/O;
- métricas de cache;
- logs;
- traces;
- correlação entre múltiplas métricas;
- métodos estatísticos;
- Machine Learning;
- modelos temporais;
- detecção de anomalias;
- propagação de falhas.

O survey destaca que o aumento anormal do tempo de resposta é um indicador comum de anomalia e que abordagens baseadas em monitoramento frequentemente utilizam latência, throughput, CPU e memória.

### Conexão direta com o AIM

Isso fornece literatura acadêmica para sustentar que as métricas atualmente consideradas não são arbitrárias:

```text
API
latência + erros + throughput

Servidor
CPU + RAM + I/O + rede

Banco
latência + conexões + CPU + memória + I/O + throughput
```

Também reforça a hipótese de que uma única métrica pode não ser suficiente e que a correlação entre sinais pode ser relevante.

---

# 5. Base acadêmica — previsão de desempenho em microserviços

## 5.1 Temporal-aware semi-supervised performance prediction and resource allocation for cloud-native microservices

**2026 — Journal of King Saud University Computer and Information Sciences / Springer**

**Fonte:** https://link.springer.com/article/10.1007/s44443-026-00981-3

O trabalho investiga previsão de desempenho em microserviços cloud-native utilizando abordagem temporal e semissupervisionada.

### Relevância

É particularmente interessante para a hipótese do AIM de utilizar:

```text
histórico temporal
      ↓
estado atual
      ↓
padrões temporais
      ↓
previsão de desempenho
```

Deve ser estudado em profundidade antes de escolher o algoritmo do AIM.

---

# 6. Base acadêmica — propagação de falhas

## 6.1 Service dependency modeling and failure propagation prediction in distributed systems based on graph neural networks

**2026 — Discover Artificial Intelligence / Springer**

**Fonte:** https://link.springer.com/article/10.1007/s44163-026-01213-3

O trabalho investiga modelagem de dependências entre serviços e previsão da propagação de falhas utilizando redes neurais baseadas em grafos e modelagem temporal.

### Relevância para o AIM

É diretamente relacionado à hipótese:

```text
Banco
  ↓
degradação
  ↓
serviço
  ↓
latência
  ↓
API
  ↓
erros
```

Isso fortalece a ideia de que o AIM pode futuramente analisar não apenas métricas isoladas, mas também **dependências e propagação temporal entre serviços**.

Essa possibilidade já aparece no pitch como uma das perguntas centrais do projeto.

---

# 7. Base acadêmica — previsão de confiabilidade

## 7.1 A comprehensive survey on intelligent software reliability prediction

**2025 — Discover Computing / Springer**

**Fonte:** https://link.springer.com/article/10.1007/s10791-025-09597-z

Survey sobre previsão de confiabilidade de software utilizando métodos tradicionais, Machine Learning e abordagens híbridas.

### Relevância

Pode servir como base para a seção de:

- software reliability;
- failure prediction;
- Machine Learning;
- avaliação de modelos;
- comparação de abordagens.

É uma referência mais ampla que o survey específico de microserviços.

---

# 8. Base acadêmica — previsão de falhas usando logs

## 8.1 Systematic Evaluation of Deep Learning Models for Log-based Failure Prediction

**2024 — Empirical Software Engineering / Springer**

**Fonte:** https://link.springer.com/article/10.1007/s10664-024-10501-4

O estudo investiga métodos de Machine Learning e Deep Learning para prever falhas utilizando dados de logs.

### Relevância

Ajuda a fundamentar a ideia de que dados de execução podem ser usados para prever falhas em tempo de execução.

No AIM, porém, o foco inicial é mais amplo:

```text
métricas
+
séries temporais
+
possivelmente logs/traces
```

Portanto, esta referência deve ser usada como base complementar, e não como justificativa exclusiva do desenho atual.

---

# 9. ITIL, COBIT, CMMI e SEI

## 9.1 ITIL

**Papel:** gestão de serviços de TI.

Pode ajudar a fundamentar conceitos como:

- incidentes;
- problemas;
- disponibilidade;
- melhoria contínua;
- gerenciamento de serviços.

### Uso no AIM

**Secundário.**

Não é a melhor fonte para justificar diretamente:

> "CPU, RAM e latência foram escolhidas como features."

---

## 9.2 COBIT

**Papel:** governança, controles, riscos e gestão de TI.

Pode ajudar na discussão de:

- risco;
- governança;
- controles;
- indicadores;
- alinhamento entre TI e negócio.

### Uso no AIM

**Secundário.**

Não deve ser a principal base para a definição das métricas de ML.

---

## 9.3 CMMI

**Papel:** maturidade e melhoria de processos.

É útil para discutir maturidade organizacional e de processos de desenvolvimento/serviços.

### Uso no AIM

**Baixa prioridade.**

Não possui conexão tão direta com a definição das métricas operacionais ou do target preditivo.

---

## 9.4 SEI

**Papel:** instituto de pesquisa ligado à Carnegie Mellon University e historicamente associado ao desenvolvimento do CMM/CMMI.

### Uso no AIM

**Baixa prioridade.**

É mais relevante para a história e fundamentos de engenharia de software/processos do que para o problema específico de previsão de degradação do AIM.

---

# 10. Matriz de fundamentação

| Elemento do AIM | Base mais adequada |
|---|---|
| Qualidade de software | ISO/IEC 25010 |
| Medição da qualidade | ISO/IEC 25010 |
| Gestão de serviços | ISO/IEC 20000-1 |
| Monitoramento de serviços | ISO/IEC 20000-1 |
| Latência | SRE / SLI + literatura acadêmica |
| Erros | SRE / SLI + literatura acadêmica |
| Throughput | SRE / SLI |
| Disponibilidade | SRE / SLI |
| CPU | SRE / Golden Signals + literatura |
| Memória | Literatura de anomalias/microserviços |
| I/O | Literatura de anomalias/microserviços |
| Correlação entre métricas | Literatura acadêmica de observabilidade |
| Dependência entre serviços | Literatura de propagação de falhas |
| Detecção de anomalias | Literatura acadêmica |
| Forecasting | Literatura de séries temporais/predição |
| Classificação de falhas | Literatura de ML |
| Ground truth | Metodologia experimental + literatura de failure prediction |
| False positive / false negative | Literatura de classificação/anomaly detection |
| Tempo de antecipação | Literatura de previsão + definição experimental |
| Governança | COBIT |
| Gestão de incidentes/problemas | ITIL |
| Maturidade de processos | CMMI |

---

# 11. O que NÃO devemos afirmar

As fontes pesquisadas não sustentam diretamente afirmações como:

> "ISO/IEC 25010 determina que devemos utilizar CPU, RAM e latência."

ou:

> "A ISO define que o target deve ser indisponibilidade nos próximos 5 minutos."

ou:

> "SRE prova que aumento de CPU causa indisponibilidade."

Essas seriam extrapolações.

O caminho cientificamente mais correto é:

```text
Norma / literatura
       ↓
define ou sustenta a importância
de determinadas propriedades
       ↓
métricas observáveis
       ↓
dados experimentais
       ↓
análise estatística
       ↓
identificação de padrões
       ↓
definição do target
       ↓
Machine Learning
       ↓
avaliação
```

---

# 12. Como isso pode fundamentar os três serviços

## API

### Métricas candidatas

- latência;
- erro;
- requests/s;
- timeout;
- disponibilidade.

### Fundamentação

**SRE:** latência, erros, throughput e disponibilidade.

**ISO/IEC 25010:** propriedades de qualidade mensuráveis.

**Literatura de microserviços:** latência, throughput e múltiplos sinais como indicadores de anomalias.

---

## Banco de dados

### Métricas candidatas

- latência de queries;
- erros;
- conexões;
- CPU;
- memória;
- I/O;
- throughput;
- timeout.

### Fundamentação

**SRE:** sistemas de armazenamento tendem a observar latência, disponibilidade e durabilidade.

**Literatura de microserviços/anomalias:** CPU, memória, I/O, latência e throughput aparecem como sinais monitorados.

**Pesquisa específica de banco:** ainda deve ser feita antes de fechar os targets.

---

## Servidor

### Métricas candidatas

- CPU;
- RAM;
- disco;
- I/O;
- rede;
- processos;
- load;
- disponibilidade.

### Fundamentação

**SRE Golden Signals:** saturação é uma das quatro categorias centrais de monitoramento.

**Literatura de anomalias:** CPU, memória, rede e I/O aparecem em abordagens de monitoramento e detecção.

**Pesquisa específica de infraestrutura:** ainda deve ser feita para transformar essas métricas em targets cientificamente justificados.

---

# 13. Lacunas que ainda precisamos pesquisar

Esta pesquisa de discovery já fornece uma boa base, mas **não fecha ainda a fundamentação do AIM**.

As próximas pesquisas deveriam responder:

### API

- Quais padrões precedem aumento de latência?
- Quais padrões precedem indisponibilidade?
- Qual relação existe entre throughput e latência?
- Qual relação entre erro, timeout e disponibilidade?
- Existem estudos que utilizam janela de 1, 5 ou 10 minutos?
- Como definir um evento de degradação?

### Banco

- Quais métricas são mais relevantes para degradação?
- Como CPU, memória, I/O e conexões afetam latência?
- Quais sinais precedem timeout?
- Quais padrões precedem indisponibilidade?

### Servidor

- Como CPU, RAM, I/O e rede se relacionam?
- Quais sinais indicam saturação?
- Como diferenciar utilização alta normal de degradação?
- Quais indicadores possuem valor preditivo?

### ML

- Forecasting versus classificação;
- anomaly detection;
- modelos supervisionados;
- modelos não supervisionados;
- séries temporais multivariadas;
- definição de janela temporal;
- definição do horizonte;
- class imbalance;
- avaliação de falsos negativos;
- lead time / tempo de antecipação.

---

# 14. Prioridade de leitura

Eu priorizaria nesta ordem:

### Alta prioridade

1. **ISO/IEC 25010:2023**
2. **ISO/IEC 20000-1:2018**
3. **Google SRE — SLO**
4. **Google SRE — Four Golden Signals**
5. **Survey 2026 sobre anomaly detection e root-cause em microserviços**

### Segunda prioridade

6. **Temporal-aware performance prediction em microserviços**
7. **Failure propagation prediction**
8. **Software reliability prediction survey**
9. **Log-based failure prediction**

### Contextual

10. ITIL
11. COBIT
12. CMMI
13. SEI

---

# 15. Conclusão do discovery

A fundamentação do AIM pode ser construída em quatro camadas:

```text
┌───────────────────────────────────────┐
│           BASE NORMATIVA              │
│                                       │
│ ISO/IEC 25010                         │
│ ISO/IEC 20000-1                       │
└───────────────────┬───────────────────┘
                    ↓
┌───────────────────────────────────────┐
│             BASE TÉCNICA              │
│                                       │
│ SRE / SLI / SLO                       │
│ Golden Signals                        │
└───────────────────┬───────────────────┘
                    ↓
┌───────────────────────────────────────┐
│          BASE ACADÊMICA               │
│                                       │
│ Anomaly Detection                     │
│ Failure Prediction                    │
│ Time Series                           │
│ Failure Propagation                   │
│ Microservices                         │
└───────────────────┬───────────────────┘
                    ↓
┌───────────────────────────────────────┐
│          METODOLOGIA DO AIM           │
│                                       │
│ Métricas → Ground Truth → Features   │
│ → Target → ML → Avaliação             │
└───────────────────────────────────────┘
```

A principal conclusão é:

> **As normas fundamentam por que qualidade, desempenho, confiabilidade e monitoramento devem ser tratados e medidos. A literatura técnica fundamenta quais indicadores são utilizados na prática. A literatura acadêmica fundamenta a análise, detecção e previsão. O próprio experimento do AIM deve determinar quais métricas realmente possuem poder preditivo e qual definição de target é adequada.**

Isso é particularmente importante porque o pitch já estabelece que vocês **não querem assumir previamente quais métricas são preditivas**; elas serão coletadas e analisadas para descobrir quais sinais realmente possuem relação com os eventos de degradação. [Fonte: pitch AIM, linhas 214–228.]

## Referências principais

- ISO/IEC 25010:2023 — https://www.iso.org/standard/78176.html
- ISO/IEC 20000-1:2018 — https://www.iso.org/standard/70636.html
- Google SRE — Service Level Objectives — https://sre.google/sre-book/service-level-objectives/
- Google SRE — Monitoring Distributed Systems — https://sre.google/sre-book/monitoring-distributed-systems/
- Google SRE — Measuring Reliability — https://sre.google/resources/practices-and-processes/measuring-reliability/
- Barata et al. (2026), *Anomaly detection and root-cause identification in microservices: a survey* — https://link.springer.com/article/10.1007/s10586-026-06095-9
- Cao, Hao & Xia (2026), *Temporal-aware semi-supervised performance prediction and resource allocation for cloud-native microservices* — https://link.springer.com/article/10.1007/s44443-026-00981-3
- *Service dependency modeling and failure propagation prediction in distributed systems based on graph neural networks* (2026) — https://link.springer.com/article/10.1007/s44163-026-01213-3
- *A comprehensive survey on intelligent software reliability prediction* (2025) — https://link.springer.com/article/10.1007/s10791-025-09597-z
- *Systematic Evaluation of Deep Learning Models for Log-based Failure Prediction* (2024) — https://link.springer.com/article/10.1007/s10664-024-10501-4
