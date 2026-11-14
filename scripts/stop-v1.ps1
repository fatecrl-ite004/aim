param([switch]$Database)
. (Join-Path $PSScriptRoot 'v1-common.ps1')
$processFile = Join-Path $AimRuntime 'processes.json'
if (Test-Path -LiteralPath $processFile) {
    $state = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
    if ($state.repo_root -ne $AimRepoRoot) { throw 'Manifesto de processos pertence a outro checkout.' }
    foreach ($name in @('frontend_pid', 'api_pid')) {
        $managedPid = $state.$name
        if (-not $managedPid) { continue }
        $running = Get-CimInstance Win32_Process -Filter ("ProcessId = {0}" -f [int]$managedPid)
        if ($running) {
            if (-not $running.CommandLine -or $running.CommandLine -notmatch [regex]::Escape($AimRepoRoot)) {
                throw "PID $managedPid nao corresponde ao checkout AIM; nenhum processo estranho foi encerrado."
            }
            Stop-Process -Id ([int]$managedPid)
            Write-Output "Processo AIM encerrado: $name."
        }
    }
}
if ($Database) {
    Invoke-AimNative 'docker' @('compose', '--env-file', $AimEnvFile, '-f', (Join-Path $AimRepoRoot 'infra/compose.v1.yml'), 'stop', 'postgres')
    Write-Output 'PostgreSQL parado; volume preservado.'
}
