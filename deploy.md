# Executar e testar a V1 do AIM

Este guia sobe o PostgreSQL, a API FastAPI, o Collector OTLP e o frontend React. O caminho Docker mantém a fonte AIOpsArena fora da imagem e do Git; ela é montada em modo somente leitura na API que coordena a demonstração e no runner opcional de verificação.

## Pré-requisitos para Docker

- Docker Desktop iniciado com contêineres Linux e suporte ao Docker Compose v2.
- Python e Node.js só são necessários para o caminho alternativo executado no host.
- O recorte local do AIOpsArena aprovado para a demonstração, já extraído. Não copie o dataset para este repositório.
- A porta `55432` disponível para PostgreSQL, `8080` para a interface e `4318`/`13133` para OTLP e saúde do Collector. As portas publicadas escutam apenas em `127.0.0.1`.

## Subir a composição inteira em Docker

No PowerShell, a partir da pasta raiz do repositório:

```powershell
if (-not (Test-Path .env.v1)) { Copy-Item .env.v1.example .env.v1 }
notepad .env.v1
```

Se `.env.v1` já existir, preserve-o e não substitua suas credenciais. Defina uma senha em `AIM_POSTGRES_PASSWORD`, a mesma senha no DSN `AIM_DATABASE_URL`, e ajuste `AIM_DATASET_ROOT` para a pasta do AIOpsArena somente ao criar a configuração pela primeira vez. O banco usa o volume nomeado `aim-v1-pgdata`; alterar a variável da senha não troca a senha de um banco já inicializado. Preserve a senha que corresponde ao volume existente. O arquivo `.env.v1` é local e não deve ser versionado.

### Exemplo de `.env.v1` preenchido

Após copiar `.env.v1.example`, um exemplo para a composição Docker no Windows é:

```dotenv
AIM_POSTGRES_PASSWORD=senha-local-exemplo-123
AIM_POSTGRES_PORT=55432
AIM_DATABASE_URL=postgresql://aim:senha-local-exemplo-123@127.0.0.1:55432/aim
AIM_API_URL=http://127.0.0.1:8000
AIM_DATASET_ROOT=C:\datasets\AIOpsArena
AIM_WEB_PORT=8080
AIM_OTLP_PORT=4318
AIM_OTLP_HEALTH_PORT=13133
```

Substitua a senha de exemplo por uma senha sua nas **duas** linhas e troque `C:\datasets\AIOpsArena` pela pasta onde o dataset foi extraído. Essa pasta deve conter `Case-1\Case-1`; o caminho aponta para a raiz do AIOpsArena, não para um CSV individual. `AIM_POSTGRES_PORT` é a porta do banco publicada no Windows; `AIM_WEB_PORT`, `AIM_OTLP_PORT` e `AIM_OTLP_HEALTH_PORT` publicam interface, ingestão OTLP e saúde do Collector. O Compose configura internamente os endereços entre contêineres. Não coloque `.env.v1` no Git.

Se você seguir a seção **Executar tudo sem Docker no Windows** abaixo, mantenha a mesma pasta do dataset e use a porta do PostgreSQL instalado no host, normalmente `5432`. Nesse caso, substitua as linhas de conexão por:

```dotenv
AIM_POSTGRES_PORT=5432
AIM_DATABASE_URL=postgresql://aim:senha-local-exemplo-123@127.0.0.1:5432/aim
AIM_DEMO_API_URL=http://127.0.0.1:8000
AIM_OTLP_METRICS_ENDPOINT=http://127.0.0.1:4318/v1/metrics
```

No modo sem Docker, a senha do DSN deve ser a mesma definida para o usuário `aim` no PostgreSQL local. `AIM_WEB_PORT`, `AIM_OTLP_PORT` e `AIM_OTLP_HEALTH_PORT` não configuram os processos iniciados no host; as portas deles estão nos comandos e em `infra/otel-collector.host.yaml`.

Suba os serviços, incluindo a migração do esquema:

```powershell
docker compose --env-file .env.v1 -f infra/compose.v1.yml -f infra/compose.docker.yml --profile full up --build -d --wait
```

Abra `http://127.0.0.1:8080`. Confira a prontidão da API, PostgreSQL e Collector:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health/ready
Invoke-RestMethod http://127.0.0.1:13133/
docker compose --env-file .env.v1 -f infra/compose.v1.yml -f infra/compose.docker.yml ps
```

O `health/ready` deve retornar `ready`; o endpoint do Collector deve responder com status saudável. O endpoint OTLP publicado em `127.0.0.1:4318` também pode ser usado por um emissor OTLP/HTTP Protobuf compatível.

## Iniciar a demonstração pela interface

Com a composição pronta, abra `http://127.0.0.1:8080` e use **Iniciar demonstração** na seção de replay histórico. A API cria uma nova execução, lê o recorte AIOpsArena local e envia as amostras por OTLP/HTTP Protobuf ao Collector. Cada marco só avança depois que a API receptora confirma a persistência no PostgreSQL; as transformações de 15 s e 60 s são gravadas separadamente. A interface consulta o andamento da execução e permite abrir o replay assim que seu identificador estiver disponível. Não há comando de script necessário para esse percurso.

Cada início autorizado cria um `replay_run_id` próprio. A lista de replays continua incluindo execuções anteriores; atualizar a página ou iniciar uma nova demonstração não apaga pontos, transformações ou anotações já persistidos. Uma execução ativa por vez evita misturar marcos de duas demonstrações. O volume `aim-v1-pgdata` preserva os históricos nos reinícios usuais da composição, desde que ela seja encerrada sem remover volumes.

O navegador não envia caminhos de arquivos nem URL de ingestão. A API usa a montagem somente leitura `/datasets/AIOpsArena`, faz o transporte para `http://collector:4318/v1/metrics` e conversa com sua rota de controle local em `http://127.0.0.1:8000`. Os arquivos de origem permanecem no caminho `AIM_DATASET_ROOT` do host definido em `.env.v1`.

## Verificar com o runner opcional

Execute o ciclo automatizado. A primeira opção inicia a composição antes do replay; acrescente `-IncludeGroundTruthAndTransform` para executar também as etapas separadas de rótulos e processamento:

```powershell
./scripts/demo-v1-docker.ps1 -StartStack -IncludeGroundTruthAndTransform
```

O script encaminha o replay pelo frontend/Nginx e pelo Collector antes de alcançar a API. A etapa `verify` compara os pontos persistidos com o recorte-fonte. Com o recorte atual do AIOpsArena, a evidência esperada é 282 pontos de origem, 3 séries lógicas, 92 janelas de 15 s e 276 células de cobertura para `counter-rates-v1`. A opção também executa `counter-rates-60s-v1`, que acrescenta 23 buckets completos e 69 células de cobertura sem modificar os pontos raw. No modo de lote, uma segunda transmissão com o mesmo identificador verifica idempotência. Os recibos JSON ficam em `.runtime/v1-docker/`.

### Demonstração progressiva com a interface aberta

Para ver os gráficos avançarem por marcos, deixe o Dashboard aberto em `http://127.0.0.1:8080` e execute o runner em outro PowerShell:

```powershell
./scripts/demo-v1-docker.ps1 -Stream -IncludeGroundTruthAndTransform
```

O modo `-Stream` divide o recorte em grupos cronológicos de 8 timestamps (24 pontos OTLP por grupo nas três séries). Cada grupo passa pelo Nginx e Collector, é confirmado pela FastAPI somente depois do commit no PostgreSQL e gera uma execução imutável `counter-rates-v1` limitada ao maior timestamp já persistido. O replay recebe incrementos cronológicos ao longo da demonstração: após o primeiro processamento, novos timestamps precisam ficar acima do watermark persistido; duplicatas idênticas em retry são idempotentes e backfill em timestamp antigo é rejeitado. Cada execução persiste o snapshot do prefixo disponível naquele marco. Quando esse prefixo fecha um novo bucket de 60 s, o runner também registra uma execução `counter-rates-60s-v1`; não cria versões vazias nem repete um bucket já fechado. O script imprime o `replay_run_id` logo após confirmar o primeiro grupo, aguarda 15 s nesse primeiro marco e 3 s entre os seguintes. O percurso leva cerca de 50 s mais o tempo de processamento. É um replay histórico acelerado; timestamps de origem não são deslocados e não há telemetria ao vivo.

`counter-rates-v1` preserva as janelas fiéis de 15 s. `counter-rates-60s-v1` agrega quatro deltas consecutivos e completos de 15 s em buckets não sobrepostos alinhados ao início de exibição: CPU = soma dos quatro deltas de segundos de CPU / 60; taxa amostrada de respostas = soma dos quatro incrementos de requests / 60; latência média = soma dos quatro deltas de duração / soma dos quatro incrementos de requests. Uma subjanela ausente, parcial, inválida ou com reset impede o valor agregado e fica registrada na cobertura/proveniência. Não há imputação nem estimativa do tráfego dentro dos 15 s; os resultados de 60 s não são detector ou modelo.

Depois que o primeiro marco e o identificador aparecerem no terminal, clique uma vez em **Atualizar replays**. Selecione no dropdown o replay cujo prefixo do ID corresponde ao identificador impresso e abra a instância. O detalhe inicia o acompanhamento automaticamente: a cada 2 s consulta os pontos brutos e lotes OTLP já persistidos, mostra a última amostra de origem e o horário em que chegou à API, e seleciona a nova execução completa da cadência escolhida para atualizar os gráficos. O rótulo permanece **Replay histórico**; janelas que ainda não chegaram representam progresso do replay. Use **Pausar acompanhamento** para inspecionar uma execução anterior e **Acompanhar ingestão** para retomar. A pausa inicial pode ser ampliada com `-InitialPauseSeconds 20` se for preciso mais tempo para abrir o detalhe.

No detalhe, escolha **Fiel · 15 s** ou **Agregada · 60 s** no seletor de transformação. A segunda visão usa CPU média de cores em 60 s, taxa média amostrada no bucket e latência média ponderada pelas respostas observadas. **Exportar pontos brutos completos** inclui o aquecimento e a amostra final necessários para reproduzir as diferenças entre counters. **Exportar derivados** preserva o `transform_run_id`, a versão e os limites das janelas selecionadas; os intervalos exportados correspondem à cadência dessa transformação.

O recibo `.runtime/v1-docker/stream.json` registra os marcos, os IDs das transformações, seus watermarks e resumos. A execução final verifica os 282 pontos de origem contra a fonte, as 92 janelas/276 estados de cobertura em 15 s e os 23 buckets/69 estados em 60 s. No recorte auditado, os 69 estados de cobertura agregada são completos: 17 buckets têm incremento positivo de CPU, e todos os 23 buckets têm incremento positivo de requests e duração. O modo progressivo não reenvia o replay completo ao fim. `-ChunkTimestamps`, `-PauseSeconds` e `-InitialPauseSeconds` ajustam a duração da demonstração; mantenha pelo menos 3 timestamps por grupo para incluir aquecimento e uma janela visível.

Para executar as etapas manuais, obtenha o identificador de `.runtime/v1-docker/replay.json` no modo de lote ou de `.runtime/v1-docker/stream.json` no modo progressivo e substitua `<REPLAY_ID>`:

```powershell
$replayId = (Get-Content .runtime/v1-docker/replay.json -Raw | ConvertFrom-Json).replay_run_id
docker compose --env-file .env.v1 -f infra/compose.v1.yml -f infra/compose.docker.yml --profile full --profile tools run --build --rm runner verify --replay-id $replayId
docker compose --env-file .env.v1 -f infra/compose.v1.yml -f infra/compose.docker.yml --profile full --profile tools run --build --rm runner import-ground-truth --replay-id $replayId
docker compose --env-file .env.v1 -f infra/compose.v1.yml -f infra/compose.docker.yml --profile full --profile tools run --build --rm runner transform --replay-id $replayId
docker compose --env-file .env.v1 -f infra/compose.v1.yml -f infra/compose.docker.yml --profile full --profile tools run --build --rm runner transform-60s --replay-id $replayId
```

Ground truth representa eventos de falha injetados na fonte; não é uma saída do AIM nem prova de detecção. Cada comando de transformação lê dados persistidos e registra uma execução versionada separadamente.

## Consultar e encerrar

Veja logs por serviço:

```powershell
docker compose --env-file .env.v1 -f infra/compose.v1.yml -f infra/compose.docker.yml logs -f api collector web
```

Encerre a aplicação preservando os dados locais do banco:

```powershell
docker compose --env-file .env.v1 -f infra/compose.v1.yml -f infra/compose.docker.yml --profile full down
```

O volume `aim-v1-pgdata` é persistente. Para reiniciar a aplicação, rode o comando `up` novamente. A remoção intencional do volume também apaga o banco e não faz parte do ciclo normal de teste.

## Executar tudo sem Docker no Windows

Este caminho executa PostgreSQL, API, Collector OTLP e frontend diretamente no host. Ele requer instalações locais independentes; não usa os arquivos Compose. A demonstração continua sendo um replay histórico do recorte AIOpsArena, e o banco mantém as execuções anteriores entre reinícios.

### Pré-requisitos sem Docker

- PostgreSQL instalado como serviço local, com `psql` disponível. A V1 foi verificada com PostgreSQL 18.1; configure a instância para aceitar conexões em `127.0.0.1:5432`.
- Python 3.14 com `venv` e `pip` disponíveis; Node.js 22.12 ou superior com npm.
- Binário `otelcol-contrib.exe` do OpenTelemetry Collector instalado localmente. Use uma distribuição que inclua os componentes `otlp`, `otlp_http` e `health_check` usados em `infra/otel-collector.host.yaml`.
- Recorte AIOpsArena extraído fora do repositório. Configure sua pasta em `AIM_DATASET_ROOT`; não copie os CSVs ou o JSON de referência para o Git.
- Portas locais livres: `5432` para PostgreSQL, `8000` para a API, `5173` para o frontend, `4318` para OTLP/HTTP e `13133` para a saúde do Collector.

Confirme as ferramentas em um PowerShell novo:

```powershell
psql --version
python --version
node --version
npm.cmd --version
& 'C:\caminho\para\otelcol-contrib.exe' --version
```

Se `psql` não estiver no `PATH`, use o executável da pasta `bin` da instalação do PostgreSQL. O mesmo vale para o Collector: substitua o caminho de exemplo pelo local do binário baixado.

### Preparar banco e dependências

Com o serviço PostgreSQL em execução, entre como administrador da instância:

```powershell
psql -U postgres -h 127.0.0.1 -p 5432 -d postgres
```

Para uma instalação nova, crie o usuário e o banco no terminal interativo do `psql`:

```sql
CREATE ROLE aim LOGIN;
\password aim
CREATE DATABASE aim OWNER aim;
\q
```

O comando `\password` solicita a senha sem gravá-la na linha de comando. Se o usuário ou banco `aim` já existir, preserve seus dados e ajuste apenas a configuração de conexão. Na raiz do repositório, crie o ambiente local e instale as dependências:

```powershell
if (-not (Test-Path .env.v1)) { Copy-Item .env.v1.example .env.v1 }
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r system/backend/requirements.txt
Push-Location frontend
npm.cmd ci
Pop-Location
notepad .env.v1
```

No `.env.v1`, configure `AIM_DATABASE_URL=postgresql://aim:<senha>@127.0.0.1:5432/aim`, usando a senha definida no `psql`, e a pasta real em `AIM_DATASET_ROOT`. Defina também:

```text
AIM_API_URL=http://127.0.0.1:8000
AIM_DEMO_API_URL=http://127.0.0.1:8000
AIM_OTLP_METRICS_ENDPOINT=http://127.0.0.1:4318/v1/metrics
```

O arquivo `.env.v1` permanece local e é ignorado pelo Git. Se a senha contiver caracteres reservados de URL, codifique-os na parte de senha de `AIM_DATABASE_URL`.

### Iniciar API, Collector e interface

Com o PostgreSQL pronto, execute na raiz do repositório:

```powershell
.\scripts\start-v1.ps1 -NoDatabase
```

O script aplica as migrations e inicia API e Vite no host. Ele grava os identificadores de processo e logs em `.runtime/v1/`. Em outro PowerShell, na mesma pasta, inicie o Collector:

```powershell
& 'C:\caminho\para\otelcol-contrib.exe' --config=infra/otel-collector.host.yaml
```

Confira os serviços:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/ready
Invoke-RestMethod http://127.0.0.1:13133/
```

Abra `http://127.0.0.1:5173` e clique em **Iniciar demonstração** no replay histórico. A API lê o recorte externo, envia os pontos ao Collector em `127.0.0.1:4318`, recebe o encaminhamento em `/v1/metrics`, persiste os pontos no PostgreSQL e publica os snapshots para os gráficos. O frontend encaminha `/api` para a FastAPI por meio do proxy do Vite. Para conferir a persistência após a demonstração:

```powershell
psql -U aim -h 127.0.0.1 -p 5432 -d aim -c 'SELECT count(*) FROM raw_metric_point;'
```

Para encerrar, pressione `Ctrl+C` no PowerShell do Collector e execute `.\scripts\stop-v1.ps1` para API e frontend. O serviço PostgreSQL e seu banco permanecem intactos. Esse percurso sem Docker está documentado a partir dos comandos e configurações do projeto; nesta máquina não foi possível executá-lo de ponta a ponta porque PostgreSQL e Collector não estão instalados no host.

### Alternativa híbrida já automatizada

Se apenas PostgreSQL estiver no Docker, `./scripts/start-v1.ps1` inicia o banco via Compose e mantém API e frontend no host. `./scripts/verify-v1.ps1` verifica esse percurso. O Collector não participa desse modo, a menos que seja iniciado separadamente com `infra/otel-collector.host.yaml` e que `AIM_OTLP_METRICS_ENDPOINT` aponte para `127.0.0.1:4318/v1/metrics`.

## O que este protótipo demonstra

A composição é o ambiente local da V1: replay histórico AIOpsArena por OTLP/HTTP Protobuf, recepção FastAPI, persistência PostgreSQL, consulta da jornada conectada do frontend e processamento batch reproduzível. Não implementa coleta contínua, cadastro de aplicações, RBAC, notificações ou detecção integrada por modelo. As outras telas ainda marcadas como mock permanecem simulações de interface; não são fluxos de negócio completos.
