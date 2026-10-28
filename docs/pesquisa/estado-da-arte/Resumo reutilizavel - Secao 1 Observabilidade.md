# Seção 1 — Observabilidade de sistemas distribuídos

## Escopo

Síntese dos três materiais da seção sobre observabilidade. O livro *Site Reliability Engineering* também está na pasta, mas foi excluído do recorte solicitado anteriormente. Os resumos distinguem estudo empírico, relato operacional e orientação conceitual.

## 1. Vani (2025) — *AI-Based Distributed Systems Observation System for Performance Optimization and Reliability Enhancement*

**Área e problema.** AIOps e observabilidade distribuída. O texto aborda telemetria fragmentada, dificuldade para prever degradações e excesso de alertas em aplicações distribuídas.

**Solução proposta.** Integra métricas, logs e traces; aplica ML para detecção e previsão de anomalias/degradações; apresenta dashboards e alertas como parte do fluxo operacional. É útil como arquitetura de referência para juntar coleta, análise e resposta.

**Resultados reportados.** O artigo descreve um caso de produção e declara TPR de 93,8%, FPR de 3,7%, antecipação de 89,4% dos eventos de degradação, redução de MTTR de 89 para 29 minutos e de 37 para 17 incidentes mensais. Não fornece dados brutos, protocolo completo de rotulagem, splits, parâmetros integrais ou desenho comparativo suficiente para reproduzir e atribuir causalmente essas mudanças.

**Como replicar/testar.** Instrumentar serviços com métricas, logs e traces; registrar incidentes, serviço, severidade e horários; separar treino/validação/teste cronologicamente; congelar limiar antes do teste; comparar com regras estáticas e operação anterior. Medir precisão, recall, falsos alertas por serviço/dia, antecedência, MTTR e custo de telemetria. Sem dados originais, reproduz-se a arquitetura e avaliam-se novos números, não se repete o caso exatamente.

**Limitação e uso.** Trate os números como alegações do estudo de caso. São úteis para motivar hipóteses, mas não como baseline garantido.

## 2. Sakinala (2025) — *Monitoring and Observability for Cloud-Native Applications*

**Área e problema.** Práticas para entender aplicações cloud-native em que serviços, contêineres e dependências mudam continuamente.

**Metodologia e solução.** Discussão/revisão técnica, sem experimento próprio nem protocolo sistemático de busca documentado. Organiza observabilidade em métricas, logs e traces; aborda instrumentação, coleta, alertas, dashboards e ferramentas cloud-native.

**Como aplicar/testar.** Definir sinais ligados a serviço e SLO; padronizar instrumentação e propagação de contexto; verificar completude, cardinalidade e atraso; criar painéis por serviço/jornada; injetar falhas para confirmar que sinais e alertas cobrem o impacto. Medir custo, ruído e capacidade de localizar origem.

**Limitação e uso.** Bom apoio para arquitetura e terminologia; não há resultados próprios que quantifiquem ganho ou provem superioridade de ferramentas.

## 3. Bissig (2024) — *Unified Application Observability in Cloud-Native Systems* (trabalho acadêmico)

**Área e problema.** Observabilidade unificada e custo de instrumentação: reunir telemetria de aplicação em uma arquitetura consultável sem ignorar seu impacto na latência e nos recursos.

**Metodologia e solução.** Síntese de literatura, entrevistas semiestruturadas (14 participantes iniciais conforme o texto), protótipos e benchmark sintético. A arquitetura usa OpenTelemetry/OTLP Collector para ingestão e ClickHouse/Grafana para armazenamento e exploração, com eventos estruturados e traces correlacionáveis.

**Como replicar.** Comparar versões instrumentada e não instrumentada sob carga k6; variar carga de 0 a 1000 RPS; avaliar Java e configuração mista Java/TypeScript; reservar aquecimento de 30 s, carga de 120 s e analisar a janela estável (~90 s); controlar hardware e configuração. Registrar p50/p95/p99, CPU, memória, throughput e volume de telemetria.

**Resultados declarados.** No cenário Java, p50 aumentou cerca de 10,7% e p99 77,5%; no cenário misto, p95 chegou a aumento de 411%, com CPU e memória elevadas. A evidência mostra que overhead depende da pilha e que a cauda da latência precisa ser medida.

**Limitação e uso.** Benchmark sintético, ambiente limitado e sem amostragem; não prevê automaticamente custo em produção. Reutilize principalmente o protocolo de medição.

## Síntese reutilizável

Correlacione os três sinais (métricas, logs e traces), conecte alerta a processo operacional mensurável e avalie o custo da própria coleta. Um experimento robusto precisa documentar dados, rótulos, splits cronológicos, configuração e baseline. Um relato de produção sem esses elementos serve como motivação arquitetural, não como garantia quantitativa.

## Fontes consultadas

Arquivos da pasta `state_of_art/seção 1`: `AI-Based Distributed Systems Observation System...pdf`; `Monitoring and Observability for Cloud-Native Applications.pdf`; `Unified Application Observability in Cloud-Native Systems.pdf`. O livro *Site Reliability Engineering* ficou fora do escopo.
