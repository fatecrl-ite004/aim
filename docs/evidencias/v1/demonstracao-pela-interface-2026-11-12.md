# Demonstração iniciada pela interface — 12/11/2026

## Percurso verificado

Com PostgreSQL, API, Collector OTLP e frontend saudáveis na composição Docker, o botão **Iniciar demonstração** da Visão geral iniciou um replay novo sem comando de ingestão no terminal. A interface abriu o detalhe assim que as primeiras séries ficaram disponíveis. Nesse ponto, a tela mostrava 24 pontos brutos, um lote OTLP confirmado e os gráficos do primeiro intervalo. O acompanhamento consulta novos marcos sem recarregar o documento.

A execução `d6d238e3-1f31-485d-a549-9da673be3415` terminou com status `completed`, 12 de 12 lotes e 282 pontos brutos no replay `47c9e6a6-cfbf-478a-bd90-4f0f4353723b`. A consulta de `/api/v1/replays` após a execução retornou 23 replays, incluindo os anteriores. A prova de reinício e de preservação de uma execução interrompida está nos recibos locais `.runtime/v1-docker/demo-restart-acceptance.json`; esses recibos contêm identificadores de execução e não precisam ser copiados ao Git.

## Verificações executadas

- Backend: 47 testes automatizados aprovados, incluindo idempotência, concorrência e recuperação após reinício.
- Frontend: 27 testes Vitest, 8 testes E2E Playwright e build de produção aprovados.
- Integração real: 1 teste Playwright contra `http://127.0.0.1:8080`, com consulta dos CSVs e comparação das transformações de 15 s e 60 s. O teste usa `AIM_FRONTEND_BASE_URL` para selecionar a instância Docker e `AIM_LIVE_REPLAY_ID` para fixar o replay verificado.
- Após a publicação da interface, `/health/ready` respondeu `ready` e o serviço web ficou saudável.

O teste E2E de atualização manteve o painel de CPU montado, conservou o valor anterior durante a nova consulta e preservou a posição de rolagem. O detalhe real foi inspecionado em desktop e largura móvel; as capturas estão em [Visão geral](dashboard-atualizado-2026-11-12.png) e [Replay de 60 s](replay-atualizado-2026-11-12.png).

## Limite da evidência

O replay acelera dados históricos do AIOpsArena. As séries derivadas são cálculos determinísticos; o evento importado é uma anotação da fonte. Esta verificação comprova transporte, persistência, consulta, exportação e comportamento de interface. Ela não mede a utilidade da solução com usuários nem o desempenho de um detector de anomalias.
