# Sistema PoC

`system/backend/aim/` contém o backend Python/FastAPI da PoC V1, a migration PostgreSQL, o receiver OTLP/HTTP Protobuf, o replayer e o processamento AIM versionado. O protótipo React está em [`frontend/`](../frontend/). A jornada local integrada passou por teste de OTLP, banco, processamento, API, UI e reinício persistente; veja o [guia de execução](../deploy.md) e os [testes de desenvolvimento](../docs/evidencias/v1/testes-desenvolvimento-2026-11-12.md).

As telas fora da jornada de replay continuam reproduzindo fluxos com dados fictícios e persistência local no navegador. A V1 conecta uma jornada histórica ao backend, não coleta telemetria ao vivo das aplicações cliente, não envia e-mail e não implementa RBAC. Só declarar a jornada conectada como validada depois de verificar o fluxo com a API/PostgreSQL reais e a recuperação após reinício.

A solução completa ainda requer definição de fontes de produção, fronteiras de rede, segurança/RBAC, inferência e requisitos de operação. A V1 acadêmica local demonstra apenas o corte de replay documentado, sem declarar validade do detector ou causalidade.
