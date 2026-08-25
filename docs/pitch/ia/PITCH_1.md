# AIM — Active Orchestration Service
## Consolidação do contexto, escopo e pitch de IA/ML

> Documento de trabalho consolidado a partir do projeto original, do BRIEF e das discussões realizadas até aqui.
>
> **Escopo atual deliberadamente limitado a:** monitorar, medir, analisar e notificar. Intervenções automáticas estão fora do escopo neste momento.

---

# 1. Identificação do projeto

- **Nome:** AIM — Active Orchestration Service
- **Equipe:** Pedro Augusto de Melo Borges, Thiago Guerra Soares e João Paulo Cruz de Almeida Lima
- **Público-alvo:** times de engenharia, DevOps e SRE que precisam agir antes que falhas afetem o usuário final
- **Tipo de aplicação:** serviço backend de observabilidade ativa
- **Plataforma:** .NET Aspire, ambiente servidor
- **Domínio:** observabilidade, confiabilidade e engenharia de software
- **Natureza:** PoC / TCC

---

# 2. Visão geral

O AIM é uma proposta de observabilidade ativa para aplicações distribuídas em .NET.

A ideia é ir além do monitoramento puramente reativo. O sistema deverá:

1. receber métricas em tempo real;
2. medir e organizar os dados;
3. analisar o comportamento dos serviços;
4. identificar quando thresholds são ultrapassados;
5. investigar padrões que possam anteceder uma degradação;
6. estimar risco de problemas futuros;
7. notificar os responsáveis.

O AIM, nesta fase, **não executará intervenções automáticas**.

O conceito atual é:

```text
Monitorar → Medir → Analisar → Prever risco → Notificar
```

A intervenção automática poderá ser considerada apenas como evolução futura.

---

# 3. Problema

Em sistemas distribuídos, métricas normalmente são utilizadas de forma reativa. Primeiro ocorre a falha ou degradação; depois os dados são analisados.

Isso cria alguns problemas:

- a detecção pode chegar tarde;
- sinais de diferentes serviços podem estar relacionados;
- equipes precisam interpretar grandes quantidades de dados;
- determinados padrões de degradação podem aparecer antes do impacto;
- thresholds tradicionais detectam o problema somente quando o limite já foi atingido.

A pergunta central do projeto é:

> **Como transformar a observabilidade em uma camada ativa capaz de analisar séries temporais, identificar padrões de risco e antecipar possíveis cenários de degradação antes que o problema atinja o usuário?**

---

# 4. Escopo atual

## Dentro do escopo

- monitoramento;
- coleta de métricas;
- dados em tempo real;
- thresholds;
- análise temporal;
- correlação entre sinais;
- análise estatística;
- investigação de modelos de Machine Learning;
- investigação do uso de LLMs;
- previsão de risco;
- notificação por e-mail;
- registro histórico para análise e treinamento.

## Fora do escopo neste momento

- alteração automática de código;
- commits automáticos;
- Pull Requests automáticos;
- execução de correções automáticas;
- GitHub Copilot SDK como agente de intervenção;
- aplicação automática de band-aids;
- automação corretiva.

A ideia é primeiro provar que o AIM consegue **observar e antecipar**.

---

# 5. Arquitetura conceitual

```text
                 Aplicações distribuídas
                         │
                         │ OTLP
                         ▼
                ┌───────────────────┐
                │       AIM         │
                │      Ingestão     │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Organização dos   │
                │ dados temporais   │
                └─────────┬─────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Banco       Servidor        API
             │            │            │
             └────────────┼────────────┘
                          ▼
                ┌───────────────────┐
                │ Monitoramento     │
                │ + Thresholds      │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Análise estatística│
                │ e temporal         │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Machine Learning  │
                │ / previsão de risco│
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Correlação entre  │
                │ serviços           │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ LLM               │
                │ interpretação      │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Notificação       │
                │ E-mail            │
                └───────────────────┘
```

Essa arquitetura é uma proposta de discussão. A ordem e a necessidade de cada camada ainda deverão ser validadas.

---

# 6. Os três serviços do PoC

O projeto será organizado por serviço:

```text
AIM
│
├── Banco de Dados
├── Servidor
└── API
```

Para cada serviço serão definidos:

1. ambiente;
2. métricas;
3. thresholds;
4. problemas comuns;
5. definição de problema;
6. objetivo de previsão;
7. dados históricos;
8. estratégia de notificação.

---

# 7. Serviço — API

## 7.1 Ambiente

Uma API rodando em ambiente controlado.

## 7.2 Métricas

Métricas inicialmente consideradas:

- latência;
- erros HTTP;
- requests por segundo / throughput;
- timeouts;
- disponibilidade / health check.

```text
API
│
├── Latência
├── Erros HTTP
├── Requests/s
├── Timeouts
└── Disponibilidade
```

Não está decidido que todas serão utilizadas pelo modelo. Primeiro serão coletadas e analisadas.

## 7.3 Problemas

Os problemas mais comuns deverão ser **mapeados em cima das métricas observadas**.

Não queremos assumir previamente quais métricas são preditivas.

A ideia é estudar:

```text
Métrica
   ↓
Comportamento
   ↓
Possível problema
```

## 7.4 Definição de problema

Inicialmente:

> Problema = ultrapassagem do limite definido para determinada métrica ou conjunto de métricas.

Exemplos conceituais:

```text
latência > threshold
```

ou:

```text
erros HTTP > threshold
```

Os valores dos thresholds ainda serão definidos.

## 7.5 O que queremos prever?

Dois objetivos principais:

### Degradação de latência

```text
latência normal
      ↓
latência aumentando
      ↓
threshold
      ↓
degradação
```

Queremos identificar o risco antes do threshold.

### Indisponibilidade

```text
API funcionando
      ↓
sinais de degradação
      ↓
erros / timeouts
      ↓
API indisponível
```

A previsão não deve afirmar certeza.

O objetivo é algo conceitualmente como:

> Existe uma probabilidade de que a API entre em uma condição de degradação ou indisponibilidade dentro de determinado horizonte.

## 7.6 Dados para previsão

Ainda a mapear:

- features;
- janelas temporais;
- métricas mais relevantes;
- histórico necessário;
- rótulos;
- horizonte de previsão.

## 7.7 Notificação

Canal definido inicialmente:

**E-mail.**

## 7.8 Histórico

Ainda a mapear.

---

# 8. Serviço — Banco de Dados

## 8.1 Ambiente

Um banco de dados rodando em ambiente controlado e sendo utilizado pela aplicação.

## 8.2 Métricas

Métricas inicialmente consideradas:

- latência de queries;
- taxa de erros;
- número de conexões;
- CPU;
- memória;
- I/O;
- throughput;
- timeouts.

```text
BANCO
│
├── Latência de queries
├── Erros
├── Conexões
├── CPU
├── Memória
├── I/O
├── Throughput
└── Timeouts
```

Assim como na API, a utilização dessas métricas em ML ainda não está definida.

## 8.3 Problemas

Os problemas comuns serão mapeados a partir das métricas.

Exemplo conceitual:

```text
conexões ↑
latência ↑
timeouts ↑
       ↓
possível sobrecarga
```

Outro exemplo:

```text
I/O ↑
latência ↑
       ↓
possível degradação
```

São hipóteses de trabalho, não conclusões.

## 8.4 Definição de problema

Inicialmente:

> Problema = ultrapassagem do limite definido para determinada métrica ou conjunto de métricas.

## 8.5 O que queremos prever?

### Degradação

```text
NORMAL
   ↓
alteração de comportamento
   ↓
degradação
   ↓
threshold
   ↓
problema
```

### Indisponibilidade / falha

```text
Banco funcionando
      ↓
degradação
      ↓
timeouts / erros
      ↓
banco indisponível
```

Objetivo:

> Estimar o risco de uma condição problemática dentro de determinado horizonte futuro.

## 8.6 Dados para previsão

Ainda a mapear:

- métricas relevantes;
- combinações de sinais;
- janelas temporais;
- features;
- histórico;
- rótulos;
- horizonte de previsão.

## 8.7 Notificação

**E-mail.**

## 8.8 Histórico

Ainda a mapear.

---

# 9. Serviço — Servidor

## 9.1 Ambiente

Um servidor rodando a aplicação em ambiente controlado.

## 9.2 Métricas

Métricas inicialmente consideradas:

- CPU;
- memória RAM;
- disco;
- I/O;
- rede;
- processos;
- load / utilização do sistema;
- disponibilidade.

```text
SERVIDOR
│
├── CPU
├── RAM
├── Disco
├── I/O
├── Rede
├── Processos
├── Load
└── Disponibilidade
```

## 9.3 Problemas

Os problemas serão mapeados em cima dos sinais observados.

Exemplo conceitual:

```text
CPU ↑
processos ↑
latência da aplicação ↑
        ↓
possível sobrecarga
```

Outro:

```text
RAM ↑ continuamente
       ↓
memória disponível ↓
       ↓
degradação
```

Esses padrões ainda precisam ser experimentalmente validados.

## 9.4 Definição de problema

Inicialmente:

> Problema = ultrapassagem do limite definido para uma métrica ou conjunto de métricas.

## 9.5 O que queremos prever?

### Degradação

```text
NORMAL
   ↓
alteração de comportamento
   ↓
degradação dos recursos
   ↓
threshold
   ↓
problema
```

### Indisponibilidade

```text
Servidor funcionando
        ↓
recursos começam a degradar
        ↓
serviços começam a apresentar problemas
        ↓
servidor indisponível
```

Objetivo:

> Identificar se os dados observados apresentam sinais de que o servidor está caminhando para uma condição de degradação ou indisponibilidade.

## 9.6 Dados para previsão

Ainda a mapear.

## 9.7 Notificação

**E-mail.**

## 9.8 Histórico

Ainda a mapear.

---

# 10. Uma distinção fundamental: detecção x previsão

Uma das principais conclusões da discussão foi que **tendência não significa acontecimento**.

Se observamos:

```text
RAM
60%
64%
68%
72%
76%
80%
```

e o threshold é 85%, não podemos afirmar:

> "A RAM vai chegar a 85%."

Podemos apenas dizer que existe uma tendência observada e que ela pode ser utilizada como evidência para uma previsão.

Portanto:

### Detecção

Pergunta:

> O problema já está acontecendo?

Exemplo:

```text
RAM > threshold
```

Resultado:

```text
problema detectado
```

### Previsão

Pergunta:

> Existe evidência suficiente de que o problema poderá acontecer?

Resultado:

```text
risco estimado
```

A previsão deve considerar incerteza.

---

# 11. Falsos positivos e falsos negativos

O projeto não deve assumir que o modelo consegue prever o futuro com certeza.

Existem dois erros principais.

## Falso negativo

O desastre acontece, mas o AIM não sinaliza.

```text
desastre aconteceu
        ↓
AIM disse "normal"
```

Esse é um erro particularmente importante porque pode deixar um incidente passar despercebido.

## Falso positivo

O AIM sinaliza risco, mas o desastre não acontece.

```text
AIM sinalizou risco
        ↓
desastre não aconteceu
```

Esse erro gera ruído e pode causar fadiga de alertas.

Portanto, o objetivo não é simplesmente maximizar a acurácia.

Precisamos medir o equilíbrio entre:

- falsos positivos;
- falsos negativos;
- precisão;
- recall;
- tempo de antecipação;
- taxa de detecção.

---

# 12. O detector determinístico continua existindo

Uma decisão importante foi não substituir o monitoramento tradicional por ML.

Teremos duas camadas:

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

Isso significa:

- o detector tradicional captura um problema que já ocorreu;
- o modelo de previsão adiciona uma camada de antecipação;
- se o modelo falhar em prever, o monitoramento determinístico continua funcionando.

O ML é, portanto, **uma camada adicional**, não o substituto do monitoramento.

---

# 13. Como definir o problema de ML

Não queremos inicialmente treinar um modelo para algo genérico como:

> "prever desastre".

Precisamos definir um evento mensurável.

Por exemplo:

> "Prever se determinada condição de desastre ocorrerá dentro dos próximos 5 minutos."

Podemos representar o alvo como:

```text
Y = 1 → desastre ocorre nos próximos 5 minutos
Y = 0 → desastre não ocorre nos próximos 5 minutos
```

Então podemos ter dados como:

```text
timestamp
CPU
RAM
latência
erros
requests
...
desastre_nos_proximos_5min
```

E investigar:

\[
P(	ext{desastre nos próximos 5 min}\mid X_t)
\]

onde:

- `X_t` = estado atual do sistema;
- o evento futuro é definido pelo ground truth;
- o horizonte de previsão precisa ser estabelecido.

---

# 14. Machine Learning — principais linhas de investigação

Ainda não foi decidido qual modelo será utilizado.

As possibilidades discutidas foram:

## 14.1 Forecasting

Prever valores futuros de uma métrica.

Exemplo:

```text
RAM atual = 78%

+1 min → previsão
+2 min → previsão
+3 min → previsão
```

Possibilidades de investigação:

- regressão;
- ARIMA;
- modelos de séries temporais;
- modelos temporais mais avançados.

A ideia é verificar se a previsão de métricas futuras pode antecipar uma violação de threshold.

---

## 14.2 Anomaly Detection

Em vez de aprender somente "desastre", o modelo pode aprender o comportamento normal.

Pergunta:

> Esse comportamento está ficando significativamente diferente do comportamento esperado?

Possibilidades:

- Isolation Forest;
- One-Class SVM;
- clustering;
- Autoencoder;
- métodos estatísticos.

Essa abordagem é interessante porque pode reduzir a dependência de grandes quantidades de exemplos rotulados de desastre.

---

## 14.3 Classificação

Se conseguirmos gerar dados rotulados:

```text
normal
degradação
desastre
```

podemos transformar o problema em classificação.

Exemplo conceitual:

```text
CPU       = 83%
RAM       = 91%
latência  = 850 ms
erros     = 7%
```

Resultado:

```text
P(desastre nos próximos 5 min) = 0.87
```

O valor seria uma estimativa probabilística, não uma certeza.

---

## 14.4 Séries temporais multivariadas

Essa é uma linha especialmente alinhada ao AIM.

Em vez de:

```text
RAM(t)
```

analisamos:

\[
X_t =
(CPU_t, RAM_t, Latência_t, Erros_t, Requests_t, ...)
\]

ao longo do tempo.

O modelo pode investigar padrões conjuntos.

Por exemplo:

```text
aumento de requests
        ↓
aumento de CPU
        ↓
aumento de latência
        ↓
aumento de erros
        ↓
possível degradação
```

---

# 15. Um modelo para cada serviço ou um modelo único?

Ainda não foi decidido.

Foram consideradas três arquiteturas.

## A — Um modelo por cenário

```text
Métricas
   │
   ├── Modelo Banco
   ├── Modelo Servidor
   └── Modelo API
```

Vantagem:

Cada modelo pode aprender características específicas do domínio.

---

## B — Um único modelo

```text
Métricas
   ↓
Modelo AIM
   ↓
Banco / Servidor / API
```

O modelo tenta aprender diferentes padrões de degradação.

---

## C — Modelo híbrido

```text
                 MÉTRICAS
                    │
                    ▼
             Detecção / análise
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        Banco    Servidor     API
          │         │         │
          ▼         ▼         ▼
       Modelo    Modelo     Modelo
```

Essa alternativa permite combinar uma camada geral com modelos específicos.

**Nenhuma dessas alternativas foi escolhida ainda.**

A decisão deverá ser baseada nos dados, nos cenários e nos experimentos.

---

# 16. Matemática no AIM

A matemática não entra apenas para "ter uma fórmula".

Ela pode ajudar a transformar os dados em evidências quantitativas.

Exemplos de linhas de investigação:

## Tendência

\[
rac{\Delta X}{\Delta t}
\]

Permite medir a velocidade de mudança de uma métrica.

Mas:

> tendência ≠ certeza.

Ela é uma evidência para previsão.

## Correlação

Podemos investigar relações entre métricas usando, por exemplo, correlação de Pearson:

\[
r =
rac{\operatorname{cov}(X,Y)}
{\sigma_X\sigma_Y}
\]

Mas:

> correlação não significa causalidade.

## Correlação temporal

Não queremos apenas saber se duas métricas variam juntas.

Podemos perguntar:

> O aumento de CPU acontece antes do aumento da latência?

Isso leva à investigação de defasagens temporais (*lags*) e cross-correlation.

---

# 17. Correlação entre serviços

Esse é um dos pontos mais interessantes do projeto.

Os serviços não são independentes.

Podemos ter:

```text
Banco
  ↓
degrada
  ↓
Serviço B
  ↓
latência aumenta
  ↓
API
  ↓
erros aumentam
```

Nesse caso, o AIM precisa considerar o contexto.

Uma métrica isolada pode não indicar desastre.

Mas a sequência e combinação dos sinais pode ser importante.

Exemplo conceitual:

```text
Database connections ↑
        ↓
Database latency ↑
        ↓
Service latency ↑
        ↓
API errors ↑
```

Uma pergunta importante do projeto passa a ser:

> **Podemos usar a relação temporal entre métricas de diferentes serviços para antecipar um problema?**

---

# 18. Onde entra o LLM?

Foi discutido que o LLM não deveria substituir o modelo estatístico/ML.

Uma divisão mais defensável é:

### ML / matemática

Responde:

> **Existe risco?**

### LLM

Responde:

> **O que está acontecendo e como podemos explicar isso para uma pessoa?**

Exemplo:

```text
ML:

risco = 91%

Sinais:
CPU +32%
RAM +18%
latência +240 ms
erros +4,2%
requests +27%
```

O LLM poderia transformar esses sinais em uma explicação contextual:

> O serviço apresenta aumento simultâneo de consumo de CPU, memória, latência e taxa de erros. O padrão observado é compatível com degradação progressiva.

A ideia é:

```text
Dados
 ↓
Matemática / ML
 ↓
risco
 ↓
LLM
 ↓
interpretação
 ↓
notificação
```

Isso evita colocar um LLM como uma "caixa preta" responsável por decidir sozinho se haverá um desastre.

---

# 19. Pitch de IA / Machine Learning

## Problema

O monitoramento tradicional consegue dizer:

> "O problema já aconteceu."

O AIM quer responder também:

> **"Existe algum padrão nos dados indicando que podemos estar caminhando para um problema?"**

---

## Proposta

O AIM combina:

- observabilidade em tempo real;
- thresholds;
- séries temporais;
- análise estatística;
- correlação entre métricas;
- Machine Learning;
- eventualmente LLMs para interpretação;
- notificações.

A proposta não é eliminar o monitoramento tradicional.

É adicionar uma camada de inteligência capaz de analisar o comportamento histórico e atual dos sistemas.

---

## Exemplo

Imagine:

```text
API

Latência:
200 → 230 → 270 → 310 → 360 ms

CPU:
50% → 58% → 64% → 71% → 77%

Erros:
0,5% → 0,8% → 1,2% → 2% → 3%
```

Nenhuma métrica necessariamente atingiu o threshold.

O monitor tradicional pode não emitir um alerta.

O AIM poderia analisar:

- tendência;
- velocidade de mudança;
- comportamento histórico;
- relação entre métricas;
- relação com outros serviços.

E então produzir:

```text
Risco estimado de degradação:
ALTO
```

Não significa:

> "A API certamente irá falhar."

Significa:

> **"Os dados atuais apresentam um padrão compatível com risco elevado de degradação dentro do horizonte analisado."**

---

# 20. O grande desafio científico

O principal desafio não é simplesmente escolher um algoritmo.

É responder:

> **Como construir dados que permitam ao modelo aprender o que acontece antes de um desastre?**

Para isso precisamos definir:

1. o que é um desastre;
2. quais thresholds representam problema;
3. quais cenários serão provocados;
4. quanto tempo antes queremos prever;
5. quais métricas estarão disponíveis;
6. como gerar/registrar dados históricos;
7. como definir o ground truth;
8. como medir falso positivo;
9. como medir falso negativo;
10. como medir o tempo de antecipação.

---

# 21. Próxima etapa de pesquisa

Antes de escolher modelos, precisamos mapear os três cenários de desastre.

## API

Precisamos pesquisar:

- problemas comuns;
- métricas associadas;
- padrões que precedem indisponibilidade;
- padrões que precedem aumento de latência;
- como provocar os problemas no ambiente controlado.

## Banco de Dados

Precisamos pesquisar:

- problemas comuns;
- métricas associadas;
- padrões que precedem degradação;
- padrões que precedem indisponibilidade;
- como provocar os problemas no ambiente controlado.

## Servidor

Precisamos pesquisar:

- problemas comuns;
- métricas associadas;
- padrões que precedem degradação;
- padrões que precedem indisponibilidade;
- como provocar os problemas no ambiente controlado.

---

# 22. Perguntas abertas

Estas são as principais perguntas que permanecem abertas:

### Dados

- Quais métricas realmente precisamos coletar?
- Qual frequência de coleta?
- Quanto histórico armazenar?
- Como organizar as séries temporais?
- Como lidar com valores ausentes?
- Como normalizar métricas de serviços diferentes?

### Thresholds

- Como definir os thresholds?
- Thresholds serão fixos ou adaptativos?
- Como diferenciar comportamento normal de anormal?
- Um threshold deve ser individual ou composto?

### Matemática

- Quais métodos de análise temporal utilizar?
- Como medir tendência?
- Como detectar mudanças de comportamento?
- Como medir correlação entre serviços?
- Como lidar com correlação temporal?
- Como transformar essas medidas em features?

### Machine Learning

- Precisamos de dados rotulados?
- Qual será o ground truth?
- Um modelo por serviço ou um modelo único?
- Forecasting, classificação, anomaly detection ou combinação?
- Qual horizonte de previsão?
- Como avaliar o modelo?
- Como minimizar falsos negativos?
- Qual quantidade de dados é necessária?

### LLM

- O LLM realmente agrega valor?
- Deve interpretar os resultados do ML?
- Deve gerar explicações?
- Pode correlacionar informações contextuais?
- Como impedir que ele invente conclusões?
- Quais informações devem ser fornecidas ao LLM?

### Correlação

- Como relacionar Banco → Servidor → API?
- Como considerar atraso temporal entre sinais?
- Como diferenciar correlação de causalidade?
- Podemos identificar padrões de cascata?

### Notificação

- O que deve gerar alerta?
- Threshold ultrapassado?
- Risco previsto?
- Ambos?
- Como evitar excesso de notificações?
- Qual informação deve estar no e-mail?

---

# 23. Estado atual do projeto

Neste momento, o AIM está conceitualmente dividido em:

```text
┌────────────────────────────────────────────┐
│              OBSERVABILIDADE               │
│                                            │
│  Monitorar → Medir → Armazenar             │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│                 ANÁLISE                    │
│                                            │
│ Thresholds → Estatística → Séries temporais│
│             → Correlação                   │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│              INTELIGÊNCIA                  │
│                                            │
│ Forecasting / Anomaly Detection /          │
│ Classification / modelos temporais        │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│             CONTEXTO / LLM                 │
│                                            │
│ Interpretação e explicação dos sinais      │
└──────────────────────┬─────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────┐
│               NOTIFICAÇÃO                  │
│                                            │
│                    E-mail                  │
└────────────────────────────────────────────┘
```

---

# 24. Princípio central do AIM

A proposta pode ser resumida em:

> **O AIM não deve simplesmente detectar que um sistema está com problemas. Ele deve estudar o comportamento dos dados ao longo do tempo para identificar evidências de que o sistema pode estar caminhando para uma condição de degradação.**

E existe uma distinção fundamental:

```text
DETECÇÃO
"O problema já aconteceu."

versus

PREVISÃO
"Os dados indicam risco de que o problema aconteça."
```

A previsão sempre envolve incerteza.

Portanto, o AIM deve trabalhar com **risco/probabilidade**, e não com afirmações determinísticas sobre o futuro.

---

# 25. Evolução futura

A versão inicial está deliberadamente limitada a:

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

Uma possível evolução futura seria:

```text
Monitorar
    ↓
Medir
    ↓
Analisar
    ↓
Prever
    ↓
Notificar
    ↓
Intervir
```

A etapa de intervenção automática, incluindo integração com Git e agentes, fica como possibilidade futura e não faz parte do escopo atual.
