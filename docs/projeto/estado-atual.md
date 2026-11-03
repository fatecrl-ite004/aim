# Estado atual do AIM

**Atualizado em:** 3 de novembro de 2026
**Identidade:** AIM — Active Intelligent Monitoring  
**Título do TCC:** *AIM: Uma análise multivariada de anomalias temporais em infraestruturas computacionais*.

## Objetivo e direção

O AIM é uma pesquisa aplicada e prova de conceito para analisar anomalias temporais multivariadas em métricas de infraestrutura e relacioná-las ao comportamento observado em APIs e aplicações web. A proposta inclui uma aplicação web com visualizações, indicadores de saúde e controle de acesso por perfil (RBAC), para apoiar a investigação por pessoas.

A pesquisa avaliará se a análise temporal conjunta ajuda a identificar degradações, contextualizar sinais e, em cenários rotulados, apontar risco antes do início de um evento. A capacidade de antecipação, a utilidade operacional e qualquer ganho de desempenho são hipóteses a testar, não resultados ou funcionalidades garantidos.

## Escopo atual

- Receber métricas de infraestrutura e aplicação/API por OTLP.
- Organizar séries com timestamps e atributos que permitam análise temporal por serviço, componente ou cenário.
- Investigar métodos estatísticos e de aprendizado de máquina para detecção de anomalias.
- Relacionar temporalmente sinais de infraestrutura com efeitos observados em APIs, sem presumir causalidade por correlação.
- Apresentar séries, intervalos, scores, indicadores e contexto em aplicação web com RBAC.
- Avaliar detecção, eventual antecipação e apoio à investigação em cenários experimentais controlados.

Logs, traces e topologia podem ser complementos se houver disponibilidade e justificativa experimental. Não são requisitos assumidos para o núcleo baseado em métricas.

## Limites e interpretação

Limites estáticos e variáveis são alternativas a avaliar conforme o cenário. A literatura local apresenta motivação para scoring contextual em certos contextos, mas isso não demonstra que qualquer limite dinâmico seja superior de forma universal. Definição e calibração devem usar treino/validação, nunca o conjunto final de teste.

Detecção de anomalia, previsão de valores futuros, estimativa de risco, detecção de change point e RCA são objetivos distintos. O projeto deve definir para cada avaliação o alvo, horizonte, rótulos, score e métricas. Associação temporal ou precedência entre métricas não prova causalidade.

O AIM não executa correções em código ou infraestrutura, não cria commits ou pull requests e não faz deploy ou remediação autônoma. LLM, se investigado, será complementar à apresentação de evidências já produzidas; não é decisor nem funcionalidade garantida.

## Abordagens em investigação

O capítulo do TCC menciona autoencoders, LSTM, modelos baseados em grafos, filtragem de métricas por similaridade vetorial, retreinamento diante de mudanças e validação temporal com medidas *event-wise*. TopoMAD e InterFusion também aparecem nas sínteses locais como referências candidatas para dependências topológicas, temporais ou entre métricas. Nenhum desses métodos está fixado como escolha final: são linhas de pesquisa a comparar com baselines simples e sob os dados e cenários definidos.

## Avaliação necessária

Definir cenários e ground truth; separar períodos cronologicamente em treino, validação e teste; ajustar normalização, hiperparâmetros e limiares sem consultar o teste; comparar baselines sob protocolo igual; relatar medidas pontuais e por evento, falsos alertas por tempo, atraso, custo e limitações. Eventuais afirmações de antecipação precisam de horizonte e regra de correspondência explícitos. Ablações devem estimar a contribuição de cada grupo de métricas ou componente opcional.

## Em aberto

- Cenários, eventos e protocolo de rotulagem.
- Métricas, frequência, alinhamento, retenção e tratamento de lacunas.
- Baselines, modelos, scores e limiares por cenário.
- Definições separadas para detecção, previsão, risco, change point e diagnóstico.
- Protocolo temporal, métricas event-wise, tolerância e avaliação de drift.
- Valor incremental dos sinais de infraestrutura em relação aos de API.
- Requisitos da aplicação web, perfis, visualizações e fluxo de investigação.
- Custo de instrumentação, processamento e armazenamento.

## Implementação de frontend demonstrativo

Em 3 de novembro de 2026 foi incorporado em `frontend/` um mock React navegável com cenários e dados simulados. Ele permite explorar os fluxos de interface documentados, incluindo serviços, métricas de exemplo, incidentes simulados, notificações e auditoria local. O estado é salvo no navegador. O mock não implementa backend, coleta OTLP, envio real de e-mail, autenticação/RBAC, detecção analítica nem comunicação com serviços monitorados. Sua existência não altera as hipóteses de pesquisa nem demonstra desempenho ou eficácia operacional. Consulte o [README do frontend](../../frontend/README.md).

## Relação com documentos anteriores

`archive/aim_old/BRIEF.docx`, `archive/aim_old/MVP-SCOPE.docx` e `archive/aim_old/PRD.docx` registram a concepção inicial de orquestração e intervenção automática. São documentos históricos. Para a direção acadêmica vigente, considerar este estado, `AIM capítulo 1 (1 bimestre) (3).docx` e o README atualizado.



