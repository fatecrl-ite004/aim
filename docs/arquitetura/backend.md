# Backend — responsabilidades conceituais

O escopo pressupõe recepção e organização de métricas, disponibilização de resultados analíticos à aplicação web e controle de acesso RBAC. A existência de um backend como processo implantável, os limites de API, autenticação, persistência, retentativas, filas e tecnologias ainda não estão decididos.

## Questões a especificar

- Fonte, autenticação e configuração de endpoints OTLP.
- Validação de timestamps, atributos, unidades, duplicatas e lacunas.
- Retenção, consulta histórica, isolamento de dados e política de acesso.
- Interface entre ingestão, pesquisa executável, inferência e interface.
- Requisitos de segurança, disponibilidade, desempenho e operação.

Esta página não declara serviço/backend implementado nem escolhe arquitetura de implantação.
