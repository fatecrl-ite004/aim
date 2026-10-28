# Requisitos e necessidades documentados

**Status:** síntese de direção a partir dos documentos do projeto; não é backlog aprovado nem contrato de aceite.

## Capacidades previstas na direção

| ID | Necessidade/capacidade | Evidência na documentação | Estado |
| --- | --- | --- | --- |
| RQ-01 | Receber métricas OTLP de infraestrutura e APIs com seus timestamps e atributos de origem. | Visão e escopo do AIM. | Prevista; instrumentação e atributos pendentes. |
| RQ-02 | Organizar séries para análise temporal conjunta. | Estado atual e pergunta de pesquisa. | Prevista; alinhamento, frequência e lacunas pendentes. |
| RQ-03 | Exibir séries, eventos, scores e contexto em aplicação web. | Direção do TCC e cenários. | Prevista; interação e telas pendentes. |
| RQ-04 | Restringir acesso por perfil (RBAC). | Direção do TCC. | Prevista; perfis e regras pendentes. |
| RQ-05 | Apoiar investigação humana sem executar remediação. | Escopo atual. | Limite explícito; fluxo operacional ainda pendente. |

## Requisitos de avaliação

- Definir eventos e rótulos observáveis antes de comparar métodos.
- Separar treino, validação e teste cronologicamente e evitar informação de teste no ajuste de transformações e limiares.
- Comparar baselines e métodos sob dados, cenários e métricas iguais.
- Relatar métricas por ponto e por evento, tolerância de correspondência, falsos alertas, atrasos, custos e limitações.
- Não declarar causalidade a partir de correlação isolada.

## Pendências para especificação

A lista efetiva de métricas, frequência e retenção, SLIs/SLOs, critérios de alerta, telas, papéis RBAC, auditoria, disponibilidade, segurança, canais de notificação, requisitos de desempenho, volumetria e implantação não foram decididos. Devem ser especificados com as partes interessadas antes de se tornarem critérios de aceite.

Para necessidades de usuários, consulte [personas](personas.md), [mapas de empatia](mapas-de-empatia.md) e [cenários](cenarios-de-uso.md). A pasta [casos de uso](casos-de-uso/README.md) é reservada a especificações futuras; nenhum caso formal foi inventado nesta organização.
