# Backend — responsabilidades conceituais e V1 local

**Estado:** implementação vertical executada em 11/11/2026. Stack V1 local: Python/FastAPI, PostgreSQL, OTLP/HTTP Protobuf e frontend React. A composição Docker usa OpenTelemetry Collector e Nginx como proxy para o mesmo receiver/API FastAPI; o caminho host direto também permanece disponível. Consulte o [guia de execução](../../deploy.md) e os [testes de desenvolvimento](../evidencias/v1/testes-desenvolvimento-2026-11-12.md).

O escopo completo pressupõe recepção e organização de métricas, disponibilização de resultados analíticos à aplicação web e controle de acesso RBAC. Para a V1 acadêmica, foi implementada uma prova local menor: FastAPI recebe apenas o perfil de métricas escolhido em OTLP, grava pontos originais em PostgreSQL, executa processamento AIM explícito sobre dados persistidos e expõe leituras para uma jornada do frontend. A prova local não entrega autenticação/RBAC, serviço contínuo ou integração com aplicações monitoradas.

## Direção de uso

A direção futura continua sendo hospedar o AIM on-premises no ambiente do cliente e receber somente sinais de aplicações e fontes cadastradas. Na V1, a API FastAPI recebe `POST /v1/metrics` em formato OTLP/HTTP Protobuf e confirma somente após commit PostgreSQL. Na composição Docker, o Collector local encaminha as requisições sem batching, fila ou compressão; no modo host, o replayer pode falar diretamente com a API. O runner manual mantém comandos separados para ground truth e transformação. A atualização de 12/11 acrescenta `POST /api/v1/demo-runs` para iniciar a mesma sequência pela interface, com estado e progresso duráveis no PostgreSQL, um replay novo por acionamento e uma única demonstração ativa. O contrato permanece limitado à PoC local.

## Questões a especificar

- Fonte, autenticação, middleware/collector e configuração de endpoints OTLP para implantação futura, incluindo fronteira de rede e alcance a aplicações cadastradas.
- Identificação de aplicação, serviço, instância e ambiente; validação de timestamps, atributos, unidades, duplicatas, atrasos e lacunas.
- Retenção, consulta histórica, isolamento de dados e política de acesso.
- Interface entre ingestão, pesquisa executável, inferência e interface.
- Requisitos de segurança, disponibilidade, desempenho e operação.

Esta página distingue o alvo local da V1 de uma implantação futura. Não declarar nenhum componente da V1 como operacional antes de registrar execução e validação ponta a ponta.
