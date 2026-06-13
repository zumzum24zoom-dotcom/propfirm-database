# このPCをランチャー常駐用にセットアップ（管理者で実行）
#  1) 8765 を握る古い pythonw を強制終了
#  2) PFDLauncherAgent タスク登録（ログオン自動起動）
#  3) 即起動 → /api/ping 確認
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1) 旧エージェント終了
Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Write-Host "kill PID $_"; taskkill /F /PID $_ 2>$null }
Start-Sleep -Milliseconds 500

# 2) タスク登録
$pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pythonw) { $pythonw = Join-Path (Split-Path (Get-Command python).Source) "pythonw.exe" }
$action   = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$here\agent.py`"" -WorkingDirectory $here
$trigger  = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "PFDLauncherAgent" -Action $action -Trigger $trigger -Settings $settings `
    -Description "PFD Launcher background agent" -Force | Out-Null

# 3) 起動 + 確認
Start-ScheduledTask -TaskName "PFDLauncherAgent"
Start-Sleep -Seconds 2
try { Write-Host ("PING OK: " + (Invoke-WebRequest 'http://127.0.0.1:8765/api/ping' -TimeoutSec 3).Content) }
catch { Write-Host "PING FAIL: $_" }
Write-Host "完了。ホットキー Insert でサイドバー開閉。"
Read-Host "Enter で閉じる"
