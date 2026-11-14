param([string]$ReplayId)
. (Join-Path $PSScriptRoot 'v1-common.ps1')
Import-AimEnvironment
Push-Location $AimRepoRoot
try {
    $receiptPath = Join-Path $AimRuntime 'last-replay.json'
    $arguments = @('-m', 'aim.cli', 'replay', '--output', $receiptPath)
    if ($ReplayId) { $arguments += @('--replay-id', $ReplayId) }
    Invoke-AimNative $AimPython $arguments
    $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    $selectedReplay = $receipt.replay_run_id
    Invoke-AimNative $AimPython @('-m', 'aim.cli', 'verify', '--replay-id', $selectedReplay, '--output', (Join-Path $AimRuntime 'last-raw-verification.json'))
    Invoke-AimNative $AimPython @('-m', 'aim.cli', 'import-ground-truth', '--replay-id', $selectedReplay, '--output', (Join-Path $AimRuntime 'last-ground-truth.json'))
    Invoke-AimNative $AimPython @('-m', 'aim.cli', 'transform', '--replay-id', $selectedReplay, '--output', (Join-Path $AimRuntime 'last-transform.json'))
    Write-Output "Replay historico pronto: $selectedReplay. Abra Visao geral -> Replay historico AIOpsArena."
} finally { Pop-Location }
