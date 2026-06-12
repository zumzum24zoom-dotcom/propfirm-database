@echo off
setlocal
set PORT=8765
set DIR=%~dp0

REM Agent (agent.py) is normally already running via Task Scheduler
REM (register-startup.ps1). Just ask it to toggle the sidebar window.
powershell -nologo -noprofile -command "try { Invoke-RestMethod -UseBasicParsing -TimeoutSec 1 'http://localhost:%PORT%/api/ping' | Out-Null; Invoke-RestMethod -UseBasicParsing -Method Post -TimeoutSec 2 'http://localhost:%PORT%/api/window/toggle' | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel% equ 0 exit /b 0

REM Agent not running (e.g. before first registration) - start it then retry.
start "" /min pythonw "%DIR%agent.py"
powershell -nologo -noprofile -command "Start-Sleep -Milliseconds 600" >nul 2>&1
powershell -nologo -noprofile -command "try { Invoke-RestMethod -UseBasicParsing -Method Post -TimeoutSec 3 'http://localhost:%PORT%/api/window/toggle' | Out-Null } catch {}"
