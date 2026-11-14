# Backend local AIM

O receiver OTLP, os dados raw, os snapshots de transformação e o histórico são
persistidos no PostgreSQL. A demonstração progressiva pode ser acionada pela UI;
não executa comandos de shell nem recebe caminhos ou URLs do navegador.

## Controle da demonstração

- `POST /api/v1/demo-runs` com JSON `{}`: responde `202` e reserva uma execução.
  `Idempotency-Key: <UUID>` identifica a intenção do clique. Repetir a chave
  retorna a mesma execução, inclusive depois de concluída.
- `GET /api/v1/demo-runs/active`: `{ "demo_run": objeto ou null }`.
- `GET /api/v1/demo-runs/{demo_run_id}`: estado e progresso persistidos.
- `GET /api/v1/demo-runs`: as 50 execuções mais recentes.

Estados: `queued`, `running`, `completed`, `failed`. Os campos planos incluem
`replay_run_id` (nulo até registrar a fonte), `current_stage`, `total_chunks`,
`completed_chunks`, `raw_point_count`, `expected_raw_point_count`, watermark,
IDs dos snapshots 15 s/60 s, datas e `error_code`/`message` quando houver falha.
O total esperado é zero enquanto a fonte não estiver validada; a UI não deve
calcular percentual nessa etapa.

Há uma execução ativa global. O POST reserva um advisory lock PostgreSQL antes
de criar a linha queued; a thread mantém sua conexão dedicada até terminar.
Um índice único parcial reforça a restrição. Outra intenção recebe `409` com
o ID ativo. Reiniciar a API libera o lock e reconcilia execuções pendentes como
`failed/interrupted`; raw, snapshots e replays anteriores permanecem no banco.
Não há retomada automática de uma thread interrompida.

O runner compartilhado com `python -m aim.cli stream` envia os mesmos pontos
originais por OTLP/HTTP Protobuf. Depois do recibo do Collector, confirma a
persistência no PostgreSQL antes de divulgar progresso ou transformar o marco.
As transformações 15 s e 60 s são novas versões persistidas de cada prefixo.
Ground truth entra em etapa separada ao final da demonstração acionada pela UI.

## Configuração do servidor

Aplicar `python -m aim.migrate` inclui `002_demo_runs.sql`. A API precisa de:

```text
AIM_DATABASE_URL=postgresql://...
AIM_DATASET_ROOT=/datasets/AIOpsArena
AIM_DEMO_API_URL=http://127.0.0.1:8000
AIM_OTLP_METRICS_ENDPOINT=http://collector:4318/v1/metrics
AIM_DEMO_CHUNK_TIMESTAMPS=8
AIM_DEMO_PAUSE_SECONDS=3
AIM_DEMO_INITIAL_PAUSE_SECONDS=3
```

O dataset continua externo ao Git, montado somente para leitura. A primeira
execução audita os arquivos completos e pode demorar nesse estágio, sobretudo
no bind Windows/Docker. O processo guarda em memória somente o recorte original
validado (282 pontos e hashes), reutilizando-o enquanto tamanho e mtime dos
arquivos permanecerem iguais. Antes de concluir cada demonstração, relê os
arquivos para conferir novamente seus SHA-256 com o manifesto. O cache
desaparece ao reiniciar a API e não contém features calculadas antecipadamente.

Somente falhas transitórias de transporte/HTTP 429/502/503/504 têm retry curto;
o mesmo lote é idempotente. Erros de perfil 4xx não são repetidos. A operação é
uma prova local de laboratório sem autenticação/RBAC, exposta via loopback.
Não representa telemetria viva, detector validado ou causalidade.

## Verificação

```powershell
$env:PYTHONPATH='system/backend'
.\.venv\Scripts\python.exe -m pytest system/backend/tests -p no:cacheprovider -q
.\.venv\Scripts\python.exe system/backend/tests/verify_demo_jobs.py --output .runtime/v1-docker/demo-jobs-acceptance.json
```

O segundo comando usa API, Collector e PostgreSQL reais. Cria uma nova
demonstração, verifica progresso monotônico, concorrência, idempotência antes e
depois de concluir, as duas resoluções e preservação dos replays anteriores.

Para verificar recuperação de uma execução interrompida, depois do aceite:

```powershell
.\.venv\Scripts\python.exe system/backend/tests/verify_demo_jobs.py --mode prepare-restart --input .runtime/v1-docker/demo-jobs-acceptance.json --output .runtime/v1-docker/demo-before-restart.json
docker compose --env-file .env.v1 -f infra/compose.v1.yml -f infra/compose.docker.yml --profile full restart api
.\.venv\Scripts\python.exe system/backend/tests/verify_demo_jobs.py --mode check-restart --input .runtime/v1-docker/demo-before-restart.json --output .runtime/v1-docker/demo-restart-acceptance.json
```

Esse teste cria outro replay, aguarda o primeiro snapshot e reinicia somente a
API. Confere `failed/interrupted`, os pontos parciais, todos os IDs anteriores e
os hashes dos snapshots completos antes/depois. Não remove replays nem volumes.

Execução real em 12/11/2026, horário local: POST202 em 0,447 s; 12 marcos,
282 pontos raw; 276 coberturas/207 valores na resolução15s e69/69 em60s.
O aceite preservou19 replays anteriores. O teste de restart preservou os20
anteriores e o novo replay parcial, com144 raw; snapshots completos mantiveram
hashes iguais. Os recibos ficam em `.runtime/v1-docker/`, fora do Git.
