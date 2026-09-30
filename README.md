# Documento Base do Projeto — AIM (Active Intelligence Monitoring)

> Documento de trabalho consolidado a partir do projeto original, do BRIEF, das discussões realizadas e dos papers de referência selecionados.
>
> **Escopo atual deliberadamente limitado a:** monitorar, medir, analisar e notificar. Intervenções automáticas estão fora do escopo neste momento.

---

## 1. Identificação do Projeto

- **Nome:** AIM — Active Intelligence Monitoring
- **Título do TCC / Projeto:** Análise multivariada e correlação de anomalias temporais em infraestruturas computacionais
- **Equipe:** Pedro Augusto de Melo Borges, Thiago Guerra Soares e João Paulo Cruz de Almeida Lima
- **Público-Alvo:** Times de SRE, DevOps, Tech Leads e Engenharia de Software
- **Tecnologia de Ingestão:** OpenTelemetry Protocol (OTLP)
- **Natureza:** Prova de Conceito (PoC) / Trabalho de Conclusão de Curso (TCC)

---

## 2. Visão Geral e Objetivo

O **AIM** tem como objetivo aplicar o estado da arte das pesquisas em detecção de anomalias temporais e correlacionar a degradação de **infraestruturas computacionais** com o comportamento e desempenho de **APIs e aplicações web**.

O projeto adota uma visão sistêmica e multivariada — abandonando a divisão rígida por tipo de serviço — e foca no monitoramento do estado da infraestrutura como um todo, analisando o impacto que padrões de degradação geram nas camadas de aplicação.

```text
[ Infraestrutura Computacional & Aplicações Web ]
                    │ (OTLP Ingestion)
                    ▼
     [ Coleta e Tratamento de Séries Temporais ]
                    │
                    ▼
     [ Correlação Multivariada + ML / Estatística ]
                    │
                    ▼
     [ Previsão de Risco & Análise Temporal ]
                    │
                    ▼
     [ Síntese e Notificação Contextualizada (LLM) ]
```

### Escopo Atual

**Dentro do escopo:**
- Coleta e ingestão de métricas em tempo real via **OTLP (OpenTelemetry)**.
- Monitoramento do estado de recursos de infraestrutura (CPU, memória, I/O de disco, rede, etc.) e métricas de aplicações web/APIs (latência, *throughput*, taxa de erros).
- Análise multivariada de séries temporais para identificar interdependências entre estresse de infraestrutura e oscilações da aplicação.
- Aplicação de modelos estatísticos e de Machine Learning (detecção não supervisionada de anomalias / *forecasting* de degradação).
- Utilização de LLM/NLP estritamente para interpretação contextual e geração de relatórios explicativos.
- Notificação ativa dos responsáveis via e-mail.
- Registro histórico para análise e treinamento.

**Fora do escopo:**
- Intervenção automática no código (criação de Pull Requests, commits).
- Ações autônomas de remediação em infraestrutura.

---

## 3. Problema e Justificativa

Sistemas e aplicações web modernos dependem de infraestruturas complexas. Quando ocorrem falhas, o comportamento anômalo costuma ser precedido por pequenos desvios em múltiplos indicadores de infraestrutura que passam despercebidos por *thresholds* pontuais ou univariados.

1. **Falta de Correlação Causal/Temporal:** Ferramentas tradicionais exibem gráficos separados para CPU/memória do servidor e latência da aplicação, deixando para o operador humano o trabalho cognitivo de correlacionar os eventos.
2. **Reatividade e Fadiga de Alertas:** Limites fixos geram falsos positivos em horários de pico normais ou notificam quando a degradação já afetou o usuário.
3. **Volume e Complexidade dos Dados:** A alta dimensionalidade dos dados coletados inviabiliza a análise manual contínua.

**Pergunta Central do Projeto:**

> *Como utilizar o estado da arte do aprendizado de máquina e da análise de séries temporais multivariadas para correlacionar ativamente a degradação da infraestrutura computacional com o impacto em aplicações web/APIs, antecipando riscos operacionais antes da ocorrência de falhas críticas?*

---

## 4. Fundamentação Científica e Padrões Selecionados

A concepção do AIM fundamenta-se nos seguintes pilares teóricos e padrões de mercado:

1. **OpenTelemetry Protocol (OTLP):** Padrão aberto universal para unificação do transporte de métricas, garantindo portabilidade, neutralidade e adesão às práticas modernas de observabilidade em nuvem.

2. **Vani, M. (2025) — *AI-Based Distributed Systems Observation System*:** Fundamenta o fluxo de observabilidade preditiva, a integração dos pilares de telemetria e o uso de IA/NLP para relatórios explicativos de causa raiz. O estudo combina detecção não supervisionada de anomalias, deep learning, *time-series forecasting* e análise causal em sistemas distribuídos de produção.

3. **Sivaraman, H. (2022) — *Adaptive Thresholding in ML-Driven Alerting Systems for Reducing False Positives in Production Environments*:** Justifica a necessidade de *thresholds* dinâmicos e camada de ML para combater a fadiga de alertas em ambientes de produção.

4. **Choi, K. et al. (2021) — *Deep Learning for Anomaly Detection in Time-Series Data: Review, Analysis, and Guidelines*:** Provê a taxonomia de anomalias temporais (pontual, contextual e coletiva) e as diretrizes de avaliação de desempenho de modelos preditivos (Precision, Recall, F1-Score).

5. **Aminikhanghagi, S ; Cook, D (2017) — *A Survey of Methods for Time Series Change Point Detection*:** Expoe uma coletanêa de estudos para detecção de mudanças temporais suas melhores abordagens utilizando notações estatisticas

Além dessas abordagens estão sendo estudados outros papers para eventuais inclusões dentro da fundamentação científica
---

## 5. Arquitetura Conceitual

```text
              Infraestrutura Computacional & Aplicações Web
                              │
                              │ OTLP
                              ▼
                     ┌─────────────────────┐
                     │        AIM          │
                     │      Ingestão       │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  Organização dos    │
                     │  dados temporais    │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  Monitoramento      │
                     │  + Thresholds       │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  Análise estatística │
                     │  e temporal          │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  Machine Learning   │
                     │  / previsão de risco │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  Correlação entre   │
                     │  infra e serviços   │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  LLM                │
                     │  interpretação      │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  Notificação        │
                     │  E-mail             │
                     └─────────────────────┘
```

---

## 6. Decisões Conceituais

### 6.1 Thresholds Determinísticos + ML

O monitoramento baseado em *thresholds* fixos e configuráveis continuará existindo como garantia determinística. A camada de ML atuará paralelamente, fornecendo capacidade de antecipação e análise probabilística.

```text
              MÉTRICAS
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
DETECÇÃO ATUAL          PREVISÃO
      │                     │
  Thresholds               ML
      │                     │
      ▼                     ▼
  INCIDENTE            RISCO FUTURO
      │                     │
      └──────────┬──────────┘
                 ▼
             NOTIFICAÇÃO
```

### 6.2 Distinção entre Detecção e Previsão

Tendência não é certeza. O AIM trabalhará com **estimativa de risco e probabilidade** — `P(degradação nos próximos N minutos | X_t)` — evitando afirmações determinísticas sobre o futuro.

### 6.3 Papel do LLM

O LLM não tomará decisões de risco. Sua função será estritamente **traduzir os outputs numéricos e estatísticos do modelo de ML em relatórios em linguagem natural**, claros e contextualizados para a equipe de SRE/DevOps.

### 6.4 Redução de Ruído

Para reduzir excesso de alertas, serão investigados mecanismos como:
- Exigir que um threshold permaneça ultrapassado durante um período N.
- Considerar a **confiabilidade da previsão** do modelo (probabilidade + horizonte).
- Outros mecanismos de redução de ruído identificados durante a experimentação.

---

## 7. Linhas de Investigação em Machine Learning

Nenhuma abordagem foi fixada. As principais linhas a investigar são:

**Forecasting:** Prever valores futuros de métricas (ARIMA, Prophet, LSTM/seq2seq) para antecipar violações de *threshold*.

**Anomaly Detection:** Aprender o comportamento normal e identificar desvios significativos (Isolation Forest, Autoencoder, One-Class SVM, VAE).

**Classificação:** Se dados rotulados forem gerados via cenários de falha controlados, transformar o problema em classificação probabilística — `P(degradação nos próximos N min) = 0.87`.

**Séries Temporais Multivariadas:** Analisar conjuntamente `X_t = (CPU_t, RAM_t, Latência_t, Erros_t, ...)` ao longo do tempo, capturando padrões de propagação entre camadas de infraestrutura e aplicação.

---

## 8. Correlação entre Infraestrutura e Aplicação

Um dos pontos centrais do AIM é investigar a relação temporal entre métricas de infraestrutura e métricas de aplicação:

```text
Degradação de infraestrutura (CPU ↑, RAM ↑, I/O ↑)
        ↓
Aumento de latência em APIs
        ↓
Aumento de taxa de erros HTTP
        ↓
Risco de indisponibilidade
```

A pergunta fundamental:

> **Podemos usar a relação temporal entre métricas de infraestrutura e métricas de aplicação para antecipar um problema antes que ele atinja o usuário final?**

---

## 9. Falsos Positivos e Falsos Negativos

O projeto não assume que o modelo consegue prever o futuro com certeza. O objetivo não é maximizar a acurácia isolada, mas equilibrar:

- **Falso negativo:** O desastre acontece, mas o AIM não sinaliza — o erro mais crítico.
- **Falso positivo:** O AIM sinaliza risco, mas o desastre não acontece — gera fadiga de alertas.

As métricas de avaliação incluem: Precision, Recall, F1-Score, tempo de antecipação e taxa de detecção.

---

## 10. O que Permanece para Investigação

- Valores efetivos dos *thresholds* por tipo de métrica.
- Métricas mais relevantes para cada cenário de degradação.
- Frequência de coleta e janelas temporais ideais.
- Definição do *ground truth* e horizonte de previsão (N minutos).
- Escolha e validação do algoritmo de ML.
- Estratégia de correlação inter-camadas.
- Escopo de contexto fornecido ao LLM.

---

## 11. Evolução Futura

A versão inicial está deliberadamente limitada a:

```text
Monitorar → Medir → Analisar → Prever risco → Notificar
```

Uma possível evolução futura:

```text
Monitorar → Medir → Analisar → Prever → Notificar → Intervir
```

A etapa de intervenção automática fica como possibilidade futura e não faz parte do escopo atual.
