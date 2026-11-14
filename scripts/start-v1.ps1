param([switch]$NoDatabase, [switch]$NoFrontend)
. (Join-Path $PSScriptRoot 'v1-common.ps1')
Import-AimEnvironment
$processFile = Join-Path $AimRuntime 'processes.json'
$state = @{ repo_root = $AimRepoRoot; started_at = [DateTime]::UtcNow.ToString('o') }
if (Test-Path -LiteralPath $processFile) {
    $prior = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
    foreach ($name in @('api_pid', 'frontend_pid')) {
        if ($prior.$name) { $state[$name] = [int]$prior.$name }
    }
}

Push-Location $AimRepoRoot
try {
    if (-not $NoDatabase) {
        Invoke-AimNative 'docker' @('compose', '--env-file', $AimEnvFile, '-f', 'infra/compose.v1.yml', 'up', '-d', '--wait', 'postgres')
    }
    Invoke-AimNative $AimPython @('-m', 'aim.migrate')
    if (-not (Test-AimHttp 'http://127.0.0.1:8000/health/ready')) {
        $api = Start-Process -FilePath $AimPython -ArgumentList @('-m', 'uvicorn', 'aim.main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $AimRepoRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $AimRuntime 'api.stdout.log') -RedirectStandardError (Join-Path $AimRuntime 'api.stderr.log') -PassThru
        $state.api_pid = $api.Id
        $state | ConvertTo-Json | Set-Content -LiteralPath $processFile -Encoding UTF8
    }
    Wait-AimHttp 'http://127.0.0.1:8000/health/ready'
    if (-not $NoFrontend) {
        if (-not (Test-AimHttp 'http://127.0.0.1:5173')) {
            $node = (Get-Command 'node.exe').Source
            $vite = Join-Path $AimRepoRoot 'frontend\node_modules\vite\bin\vite.js'
            $front = Start-Process -FilePath $node -ArgumentList @($vite, '--host', '127.0.0.1', '--port', '5173', '--strictPort') -WorkingDirectory (Join-Path $AimRepoRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $AimRuntime 'frontend.stdout.log') -RedirectStandardError (Join-Path $AimRuntime 'frontend.stderr.log') -PassThru
            $state.frontend_pid = $front.Id
            $state | ConvertTo-Json | Set-Content -LiteralPath $processFile -Encoding UTF8
        }
        Wait-AimHttp 'http://127.0.0.1:5173'
    }
    $state | ConvertTo-Json | Set-Content -LiteralPath $processFile -Encoding UTF8
    Write-Output 'API pronta: http://127.0.0.1:8000/health/ready'
    if (-not $NoFrontend) { Write-Output 'Frontend pronto: http://127.0.0.1:5173' }
    Write-Output 'Processos gerenciados em .runtime/v1/processes.json; logs no mesmo diretorio.'
} finally { Pop-Location }
