$ErrorActionPreference = 'Stop'
$AimRepoRoot = Split-Path -Parent $PSScriptRoot
$AimRuntime = Join-Path $AimRepoRoot '.runtime\v1'
$AimEnvFile = Join-Path $AimRepoRoot '.env.v1'
$AimPython = Join-Path $AimRepoRoot '.venv\Scripts\python.exe'

function Invoke-AimNative {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Comando falhou (exit $LASTEXITCODE): $Executable" }
}

function Import-AimEnvironment {
    if (-not (Test-Path -LiteralPath $AimEnvFile)) { throw 'Execute scripts/setup-v1.ps1 primeiro; .env.v1 nao existe.' }
    foreach ($line in [System.IO.File]::ReadAllLines($AimEnvFile)) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $parts = $line -split '=', 2
        if ($parts.Length -ne 2 -or $parts[0] -notmatch '^[A-Z][A-Z0-9_]*$') { throw 'Linha invalida em .env.v1.' }
        [Environment]::SetEnvironmentVariable($parts[0], $parts[1], 'Process')
    }
    $env:PYTHONPATH = Join-Path $AimRepoRoot 'system\backend'
    [void][System.IO.Directory]::CreateDirectory($AimRuntime)
}

function Test-AimHttp {
    param([string]$Url)
    try { $null = Invoke-RestMethod -Uri $Url -TimeoutSec 2; return $true } catch { return $false }
}

function Wait-AimHttp {
    param([string]$Url, [int]$Seconds = 30)
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    do {
        if (Test-AimHttp $Url) { return }
        Start-Sleep -Milliseconds 400
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "Servico nao respondeu no prazo: $Url. Consulte .runtime/v1/*.log."
}
