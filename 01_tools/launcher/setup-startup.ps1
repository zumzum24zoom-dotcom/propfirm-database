# PFD Launcher — スタートアップ常駐の登録/解除（マシン毎に一度実行）
#
#   登録:   powershell -ExecutionPolicy Bypass -File setup-startup.ps1
#   解除:   powershell -ExecutionPolicy Bypass -File setup-startup.ps1 -Remove
#
# 作るショートカット（shell:startup）:
#   PFD Launcher Hotkey.lnk … hotkey.ahk を起動（Insert で開閉）  ※要 AutoHotkey v2
#   PFD Launcher Server.lnk … server.vbs を起動（サーバ常駐・窓なし）
param([switch]$Remove)

$launcher = $PSScriptRoot
$startup  = [Environment]::GetFolderPath('Startup')
$lnkHotkey = Join-Path $startup 'PFD Launcher Hotkey.lnk'
$lnkServer = Join-Path $startup 'PFD Launcher Server.lnk'

if ($Remove) {
  Remove-Item $lnkHotkey, $lnkServer -Force -ErrorAction SilentlyContinue
  Write-Host "解除しました（スタートアップから削除）。" -ForegroundColor Yellow
  return
}

# AutoHotkey v2 の場所を探す
$ahk = @(
  "$env:LOCALAPPDATA\Programs\AutoHotkey\v2\AutoHotkey64.exe",
  "$env:ProgramFiles\AutoHotkey\v2\AutoHotkey64.exe",
  "$env:ProgramFiles\AutoHotkey\v2\AutoHotkey.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

$ws = New-Object -ComObject WScript.Shell

if ($ahk) {
  $sc = $ws.CreateShortcut($lnkHotkey)
  $sc.TargetPath = $ahk
  $sc.Arguments  = '"' + (Join-Path $launcher 'hotkey.ahk') + '"'
  $sc.WorkingDirectory = $launcher
  $sc.Description = 'PFD Launcher — Insert で開閉'
  $sc.Save()
  Write-Host "[OK] Insert開閉を登録: $lnkHotkey" -ForegroundColor Green
} else {
  Write-Host "[skip] AutoHotkey v2 が見つかりません。`n       winget install AutoHotkey.AutoHotkey で導入後に再実行してください。" -ForegroundColor Yellow
}

$sc = $ws.CreateShortcut($lnkServer)
$sc.TargetPath = "$env:WINDIR\System32\wscript.exe"
$sc.Arguments  = '"' + (Join-Path $launcher 'server.vbs') + '"'
$sc.WorkingDirectory = $launcher
$sc.Description = 'PFD Launcher — サーバ常駐'
$sc.Save()
Write-Host "[OK] サーバ常駐を登録: $lnkServer" -ForegroundColor Green

Write-Host "`n完了。次回PC起動から有効です。今すぐ有効化するには:" -ForegroundColor Cyan
Write-Host "  ・サーバ:  wscript `"$launcher\server.vbs`""
if ($ahk) { Write-Host "  ・Insert:  `"$ahk`" `"$launcher\hotkey.ahk`"" }
