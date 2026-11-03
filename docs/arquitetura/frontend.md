# Frontend — mock demonstrativo

O repositório contém um frontend React navegável em [`frontend/`](../../frontend/). Ele materializa fluxos visuais de demonstração para visão geral, detalhes de serviço, cadastro, notificações e auditoria, usando dados fictícios definidos no próprio cliente e estado salvo no `localStorage`. As instruções para instalação e execução estão no [README principal](../../README.md) e no [README do frontend](../../frontend/README.md).

Esta implementação não coleta telemetria nem chama backend, endpoint OTel, SMTP ou serviços monitorados. Estados de falha, conectividade, métricas, incidentes e resultados de notificações são simulados. A interface não implementa autenticação ou autorização RBAC real. Ela serve como mock para exploração dos fluxos, não como produto operacional nem como evidência de eficácia analítica.

## Questões em aberto

- Quais perfis podem consultar serviços, métricas, eventos e configurações?
- Como o usuário filtra por aplicação, componente, período e cenário?
- Como score, limiar, intervalo e incerteza serão explicados?
- Quais requisitos de acessibilidade, atualização, auditoria e responsividade se aplicam?
- Como exibir associação temporal sem sugerir causalidade comprovada?
- Como o frontend será integrado à API e à ingestão ainda a especificar?

Não assumir dashboard conectado, alertas em tempo real, relatórios por LLM ou gestão operacional de incidentes como funcionalidades implementadas. Ver [requisitos](../requisitos/requisitos.md).
