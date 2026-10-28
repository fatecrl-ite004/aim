# Arquitetura — visão geral conceitual

**Status:** proposta de pesquisa; não descreve serviços implementados nem decisões de tecnologia.

```text
Métricas de infraestrutura e APIs
              │ OTLP
              ▼
Ingestão e validação dos dados
              ▼
Alinhamento temporal e preparação
              ▼
Baselines e métodos em avaliação
              ▼
Scores, eventos e associações temporais
              ▼
Aplicação web com visualizações e RBAC
              ▼
Investigação e decisão humana
```

A figura resume responsabilidades funcionais inferidas do escopo. Ela não define processos, serviços independentes, protocolos internos, filas, banco, frameworks ou implantação. Em particular, **não está decidido se inferência será um serviço independente** ou uma biblioteca/pipeline integrada. A escolha exige requisitos de latência, escala, operação e reuso ainda não especificados.

- [Frontend](frontend.md): responsabilidades e questões de interface.
- [Backend](backend.md): fronteiras conceituais, sem stack definida.
- [Pipeline analítico](pipeline-analitico.md): fluxo de dados e validação temporal.
- [Modelo de dados](dados/modelo-de-dados.md) e [dicionário](dados/dicionario-de-dados.md): conceitos preliminares, não schema físico.
- [Diagramas](diagramas/): espaço para UML, fluxos e dados quando os modelos forem especificados.
