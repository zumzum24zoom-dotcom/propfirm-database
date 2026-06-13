# PFD Launcher Agent をWindowsログオン時に自動起動するタスクスケジューラ登録
#
# 使い方: このファイルを右クリック → PowerShellで実行（管理者権限不要）
# 解除:   Unregister-ScheduledTask -TaskName "PFDLauncherAgent" -Confirm:$false

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

$pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pythonw) {
    $python = (Get-Command python -ErrorAction Stop).Source
    $pythonw = Join-Path (Split-Path $python) "pythonw.exe"
}

$action = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$here\agent.py`"" -WorkingDirectory $here
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName "PFDLauncherAgent" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "PFD Launcher background agent (clipboard history, global hotkey, local server)" `
    -Force | Out-Null

Start-ScheduledTask -TaskName "PFDLauncherAgent"

Write-Host "登録 & 起動しました。タスク名: PFDLauncherAgent"
Write-Host "ホットキー Insert でサイドバーの表示/非表示を切り替えられます。"
