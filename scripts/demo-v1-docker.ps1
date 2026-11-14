param(
    [switch]$StartStack,
    [switch]$IncludeGroundTruthAndTransform,
    [switch]$Stream,
    [int]$ChunkTimestamps = 8,
    [double]$PauseSeconds = 3,
    [double]$InitialPauseSeconds = 15
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path '.env.v1')) {
    throw 'Arquivo .env.v1 ausente. Copie .env.v1.example, ajuste a senha e AIM_DATASET_ROOT.'
}

$composeBase = @('compose', '--env-file', '.env.v1', '-f', 'infra/compose.v1.yml', '-f', 'infra/compose.docker.yml')
if ($StartStack) {
    & docker @composeBase --profile full up --build -d --wait
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao subir a composição Docker.' }
}

$base = @('compose', '--env-file', '.env.v1', '-f', 'infra/compose.v1.yml', '-f', 'infra/compose.docker.yml', '--profile', 'full', '--profile', 'tools', 'run', '--build', '--rm', 'runner')
$outputDir = Join-Path $repoRoot '.runtime/v1-docker'
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$replayPath = '/runtime/replay.json'

if ($Stream) {
    & docker @base stream --chunk-timestamps $ChunkTimestamps --pause-seconds $PauseSeconds --initial-pause-seconds $InitialPauseSeconds --output '/runtime/stream.json'
    if ($LASTEXITCODE -ne 0) { throw 'O replay progressivo ou sua transformação final falhou.' }
    $streamFile = Join-Path $outputDir 'stream.json'
    if (-not (Test-Path $streamFile)) { throw 'A execução não gerou .runtime/v1-docker/stream.json.' }
    $streamReceipt = Get-Content $streamFile -Raw | ConvertFrom-Json
    $replayId = $streamReceipt.replay_run_id
} else {
    & docker @base replay --output $replayPath
    if ($LASTEXITCODE -ne 0) { throw 'O replay pelo Collector falhou.' }
    $replayFile = Join-Path $outputDir 'replay.json'
    if (-not (Test-Path $replayFile)) { throw 'A execução não gerou .runtime/v1-docker/replay.json.' }
    $replay = Get-Content $replayFile -Raw | ConvertFrom-Json
    $replayId = $replay.replay_run_id
}
if (-not $replayId) { throw 'O recibo não contém replay_run_id.' }

& docker @base verify --replay-id $replayId --output '/runtime/verify.json'
if ($LASTEXITCODE -ne 0) { throw 'A verificação de origem contra os pontos persistidos falhou.' }

if ($IncludeGroundTruthAndTransform) {
    & docker @base import-ground-truth --replay-id $replayId --output '/runtime/ground-truth.json'
    if ($LASTEXITCODE -ne 0) { throw 'A importação separada do ground truth falhou.' }
    if (-not $Stream) {
        & docker @base transform --replay-id $replayId --output '/runtime/transform.json'
        if ($LASTEXITCODE -ne 0) { throw 'O processamento dos dados persistidos falhou.' }
        & docker @base transform-60s --replay-id $replayId --output '/runtime/transform-60s.json'
        if ($LASTEXITCODE -ne 0) { throw 'A transformação agregada de 60 s falhou.' }
    }
}

if (-not $Stream) {
    & docker @base replay --replay-id $replayId --output '/runtime/retry.json'
    if ($LASTEXITCODE -ne 0) { throw 'A tentativa idempotente do replay falhou.' }
}

$verifyPath = Join-Path $outputDir 'verify.json'
$verify = Get-Content $verifyPath -Raw | ConvertFrom-Json
Write-Host "Replay: $replayId"
Write-Host "Pontos persistidos conferidos: $($verify.verified_points)"
if ($Stream) {
    Write-Host "Marcos enviados: $($streamReceipt.chunk_count); transformação fiel: $($streamReceipt.final_transform.transform_run_id); agregada 60 s: $($streamReceipt.final_transform_60s.transform_run_id)"
}
Write-Host "Recibos locais: $outputDir"
