param(
    [string]$DatasetRoot = (Join-Path $env:USERPROFILE 'Downloads\datasets_aim\AIOpsArena'),
    [switch]$SkipFrontend
)
. (Join-Path $PSScriptRoot 'v1-common.ps1')

Push-Location $AimRepoRoot
try {
    if (-not (Test-Path -LiteralPath $AimEnvFile)) {
        $randomBytes = New-Object byte[] 24
        $crypto = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        $crypto.GetBytes($randomBytes)
        $crypto.Dispose()
        $aimLocalPassword = ([BitConverter]::ToString($randomBytes)).Replace('-', '').ToLowerInvariant()
        $lines = @(
            "AIM_POSTGRES_PASSWORD=$aimLocalPassword",
            'AIM_POSTGRES_PORT=55432',
            "AIM_DATABASE_URL=postgresql://aim:$aimLocalPassword@127.0.0.1:55432/aim",
            'AIM_API_URL=http://127.0.0.1:8000',
            "AIM_DATASET_ROOT=$DatasetRoot"
        )
        [System.IO.File]::WriteAllLines($AimEnvFile, $lines, (New-Object System.Text.UTF8Encoding($false)))
        Write-Output '.env.v1 criado com credencial aleatoria local (nao exibida).'
    } else {
        Write-Output '.env.v1 existente preservado.'
    }
    if (-not (Test-Path -LiteralPath $AimPython)) {
        Invoke-AimNative 'python' @('-m', 'venv', '.venv')
    }
    Invoke-AimNative $AimPython @('-m', 'pip', 'install', '-r', 'system/backend/requirements.txt')
    if (-not $SkipFrontend) {
        Push-Location (Join-Path $AimRepoRoot 'frontend')
        try { Invoke-AimNative 'npm.cmd' @('ci') } finally { Pop-Location }
    }
    Import-AimEnvironment
    if (-not (Test-Path -LiteralPath (Join-Path $env:AIM_DATASET_ROOT 'Case-1\Case-1'))) {
        Write-Output 'Ambiente instalado. Configure AIM_DATASET_ROOT em .env.v1 antes do replay; o dataset continua externo.'
    } else {
        Write-Output 'Ambiente instalado; dataset externo localizado. Execute scripts/start-v1.ps1.'
    }
} finally { Pop-Location }
