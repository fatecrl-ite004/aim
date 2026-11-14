# Requisitos e necessidades documentados

**Status:** requisitos de produto completo continuam como síntese de direção, não como backlog aprovado. A prova local V1 de replay tem [testes de desenvolvimento documentados](../evidencias/v1/testes-desenvolvimento-2026-11-12.md); isso não valida por extensão os requisitos de produção.

## Capacidades previstas na direção

| ID | Necessidade/capacidade | Evidência na documentação | Estado |
| --- | --- | --- | --- |
| RQ-01 | Receber telemetria selecionada de infraestrutura e APIs para aplicações cadastradas, preservando timestamps e atributos de origem. | Visão e escopo, direção preliminar e contrato OTLP da V1. | V1: replay histórico local via OTLP/HTTP Protobuf; fontes contínuas, registro de aplicações e instrumentação de produção seguem pendentes. |
| RQ-02 | Organizar séries para análise temporal conjunta. | Estado atual, pergunta de pesquisa e contrato de persistência da V1. | V1: recorte AIOpsArena definido para derivação determinística pós-ingestão; avaliação científica conjunta continua pendente. |
| RQ-03 | Exibir séries, eventos e resultados analíticos em aplicação web. | Direção do TCC e jornada V1 de replay integrada à API/PostgreSQL. | A PoC mostra métricas derivadas, cobertura e evento injetado; outras áreas são mock. Critérios de detecção continuam pendentes. |
| RQ-04 | Restringir acesso por perfil (RBAC). | Direção do TCC. | Prevista; perfis e regras pendentes. |
| RQ-05 | Apoiar investigação humana sem executar remediação. | Escopo atual. | Limite explícito; fluxo operacional ainda pendente. |

## Requisitos de avaliação

- Definir eventos e rótulos observáveis antes de comparar métodos.
- Separar treino, validação e teste cronologicamente e evitar informação de teste no ajuste de transformações e limiares.
- Comparar baselines e métodos sob dados, cenários e métricas iguais.
- Relatar métricas por ponto e por evento, tolerância de correspondência, falsos alertas, atrasos, custos e limitações.
- Não declarar causalidade a partir de correlação isolada.

## Pendências para especificação

A lista de sinais de operação contínua, frequência e retenção, SLIs/SLOs, critérios de alerta, papéis RBAC, auditoria, disponibilidade, segurança, canais de notificação, volumetria e implantação em clientes continuam pendentes. Para a V1 local, replay AIOpsArena via OTLP/HTTP Protobuf, persistência PostgreSQL e processamento batch foram executados. O caminho Docker envia pelo Collector; a API FastAPI também pode receber diretamente no caminho host. Os requisitos de produção devem ser especificados com as partes interessadas antes de se tornarem critérios de aceite.

Para necessidades de usuários, consulte [personas](personas.md), [mapas de empatia](mapas-de-empatia.md) e [cenários](cenarios-de-uso.md). A pasta [casos de uso](casos-de-uso/README.md) é reservada a especificações futuras; nenhum caso formal foi inventado nesta organização.
