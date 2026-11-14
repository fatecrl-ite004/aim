# Jornada conectada de replay histórico

**Escopo implementado:** Visão geral → entrada “Replay histórico AIOpsArena” → detalhe de serviço e instância do replay. Os serviços e identificadores desta entrada vêm da API; não são vinculados aos serviços fictícios do mock.

## Leitura e navegação

1. `GET /api/v1/replays` fornece execuções e janela histórica de exibição.
2. `GET /api/v1/replays/{id}/services` fornece os serviços e instâncias persistidos para a execução escolhida.
3. No detalhe, `GET /api/v1/replays/{id}/transforms` fornece as execuções e o `default_transform_run_id` escolhido pelo backend de forma determinística. O frontend permite selecionar outra execução completa.
4. `GET /api/v1/replays/{id}/services/{service_id}/metrics` recebe obrigatoriamente a instância, a transformação e os limites da janela. A resposta deve confirmar os mesmos quatro identificadores consultados, evitando a exibição de outra entidade ou execução.
5. `GET /api/v1/replays/{id}/events` fornece ground truth separado, filtrado pela instância selecionada.

Os timestamps Unix em nanossegundos são strings decimais. Para posicionar pontos, a interface calcula o deslocamento com `BigInt` antes da conversão para `Number`. Não desloca o período histórico para o presente. Datas, eixos e tabelas informam UTC; as janelas são `[início, fim)`.

## Métricas e limites

| Nome na API | Unidade na API | Apresentação |
| --- | --- | --- |
| `cpu_cores` | `cores` | CPU média em núcleos consumidos por intervalo, sem converter em porcentagem. |
| `success_response_rate` | `1/s` | Respostas bem-sucedidas por segundo, somente a série gRPC 0 / HTTP 200 selecionada. |
| `success_latency_mean_ms` | `ms` | Média da duração das respostas 200, sem percentis. |

Cada janela mantém seu `coverage_state` e `reason`. Zero numérico com cobertura válida é observado; valor nulo, ausência, reset ou janela sem incremento observado não vira zero. A curva é interrompida em janelas sem valor e entre intervalos descontínuos. A faixa inferior de cada gráfico codifica a cobertura, com legenda textual, tooltip acessível por foco/setas e tabela completa consultável.

`not_applicable` com `reason=no_observed_increment` significa que a latência média não é definida porque o contador amostrado não aumentou. As linhas do arquivo estão em 15 s, mas os 23 incrementos positivos de contagem/duração neste corte aparecem em 60 s. Delta zero não comprova ausência física de requisições em cada janela. `partial`, `missing` e `invalid` produzem aviso de cobertura. Nenhum desses estados é tratado como operação nominal confirmada.

O marcador **Falha de CPU injetada** representa o ground truth da fonte. Não é um alerta gerado pelo AIM, medida de degradação da API ou prova causal. A interface não apresenta taxa de erro geral, p95/p99, memória, pool de banco, predição ou detecção como dados conectados.

## Estados e verificação

A entrada e o detalhe distinguem consulta em andamento, API indisponível, ausência de replay, ausência de séries, transformação pendente, ausência de janelas e cobertura das janelas. Uma falha não ativa fallback de dados simulados. As requisições são canceladas ao sair da página ou trocar a seleção.

`tests/replay.test.ts` verifica precisão de nanossegundos e tratamento de zero, lacuna, reset e `no_observed_increment`. `tests/replay.spec.ts` usa respostas HTTP controladas exclusivamente nos testes para verificar navegação, seleção explícita de versão, descontinuidade da curva, tabela de cobertura, erro/empty e layout móvel. Esses testes não comprovam ingestão, commit ou persistência PostgreSQL; essa evidência pertence à execução integrada da V1. `tests/flows.spec.ts` preserva a regressão do mock.

O servidor Vite e o preview usam loopback. A API local padrão é `http://127.0.0.1:8000`; seu endereço pode ser configurado em `AIM_API_PROXY_TARGET`. O build estático precisa de encaminhamento `/api` pelo servidor que o servir ou de `VITE_API_BASE_URL` configurado no build com CORS correspondente.
