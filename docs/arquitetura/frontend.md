# Frontend — responsabilidades previstas

A direção do projeto prevê uma aplicação web que permita consultar séries temporais, eventos/anomalias, indicadores de saúde e contexto relevante, sob controle de acesso por perfil (RBAC). Essa descrição deriva do escopo acadêmico; não há telas, framework, API de apresentação nem implementação no repositório.

## Questões em aberto

- Quais perfis podem consultar serviços, métricas, eventos e configurações?
- Como o usuário filtra por aplicação, componente, período e cenário?
- Como score, limiar, intervalo e incerteza serão explicados?
- Quais requisitos de acessibilidade, atualização, auditoria e responsividade se aplicam?
- Como exibir associação temporal sem sugerir causalidade comprovada?

Não assumir dashboard, alertas em tempo real, relatórios por LLM ou gestão de incidentes como funcionalidades aprovadas. Ver [requisitos](../requisitos/requisitos.md).
