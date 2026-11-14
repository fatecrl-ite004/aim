param([switch]$Restart, [switch]$SkipFrontendTests)
. (Join-Path $PSScriptRoot 'v1-common.ps1')
Import-AimEnvironment
Push-Location $AimRepoRoot
try {
    Invoke-AimNative $AimPython @('-m', 'pytest', 'system/backend/tests', '-p', 'no:cacheprovider', '-q')
    $acceptanceFile = Join-Path $AimRuntime 'integration.json'
    Invoke-AimNative $AimPython @('scripts/verify_v1.py', 'run', '--output', $acceptanceFile)
    if (-not $SkipFrontendTests) {
        Push-Location (Join-Path $AimRepoRoot 'frontend')
        try {
            Invoke-AimNative 'npm.cmd' @('test')
            Invoke-AimNative 'npm.cmd' @('run', 'build')
            Invoke-AimNative 'npm.cmd' @('run', 'test:e2e')
        } finally { Pop-Location }
    }
    if ($Restart) {
        $acceptance = Get-Content -LiteralPath $acceptanceFile -Raw | ConvertFrom-Json
        $before = Join-Path $AimRuntime 'before-restart.json'
        $after = Join-Path $AimRuntime 'after-restart.json'
        $common = @('--replay-id', $acceptance.replay_run_id, '--transform-id', $acceptance.transform_run_id)
        Invoke-AimNative $AimPython (@('scripts/verify_v1.py', 'snapshot') + $common + @('--output', $before))
        & (Join-Path $PSScriptRoot 'stop-v1.ps1') -Database
        & (Join-Path $PSScriptRoot 'start-v1.ps1')
        Invoke-AimNative $AimPython (@('scripts/verify_v1.py', 'snapshot') + $common + @('--output', $after))
        Invoke-AimNative $AimPython @('scripts/verify_v1.py', 'compare', '--before', $before, '--after', $after, '--require-db-restart', '--output', (Join-Path $AimRuntime 'persistence-restart.json'))
    }
    Write-Output 'Verificacao concluida. Evidencias locais em .runtime/v1; nenhum dado de origem foi copiado.'
} finally { Pop-Location }
