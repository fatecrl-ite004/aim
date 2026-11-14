# Frontend — protótipo conectado e mock

O repositório contém um frontend React navegável em [`frontend/`](../../frontend/). A jornada **Visão geral → Replay histórico AIOpsArena → detalhe** consulta a API e mostra o replay persistido, métricas derivadas, cobertura e ground truth separado. As telas gerais de serviço, cadastro, notificações e auditoria continuam como mock, com dados fictícios definidos no cliente e estado salvo no `localStorage`. As instruções para execução estão no [guia de deploy](../../deploy.md) e no [README do frontend](../../frontend/README.md).

As telas mock não coletam telemetria nem chamam backend, endpoint OTel, SMTP ou serviços monitorados. Na jornada conectada, o frontend consulta as rotas REST da API; não envia nem transforma métricas. A interface não implementa autenticação ou autorização RBAC real e não é produto operacional nem evidência de eficácia analítica.

## Questões em aberto

- Quais perfis podem consultar serviços, métricas, eventos e configurações?
- Como o usuário filtra por aplicação, componente, período e cenário?
- Como score, limiar, intervalo e incerteza serão explicados?
- Quais requisitos de acessibilidade, atualização, auditoria e responsividade se aplicam?
- Como exibir associação temporal sem sugerir causalidade comprovada?
- Como a jornada conectada evoluirá para além do replay histórico da PoC?

Não assumir telemetria contínua, alertas em tempo real, relatórios por LLM ou gestão operacional de incidentes como funcionalidades implementadas. Ver [requisitos](../requisitos/requisitos.md).
