@echo off
setlocal
set PORT=8765
set DIR=%~dp0
set URL=http://127.0.0.1:%PORT%/01_tools/launcher/

REM 1) Already running? Check LISTENING state first — a closed loopback port does NOT
REM    refuse instantly on this OS (SYN dropped -> ~1-2s hang), so an HTTP probe here
REM    would cost a full timeout every cold start. netstat reads state in ~35ms instead.
REM    LISTENING-limited match ignores lingering TIME_WAIT sockets from a prior run.
netstat -ano | findstr "LISTENING" | findstr /c:"127.0.0.1:%PORT% " >nul
if %errorlevel% neq 0 goto start_server

REM    Something is listening — confirm it's OUR serve.py answering (warm curl ~26ms).
REM    Use 127.0.0.1 (not localhost) to skip the IPv6 ::1 fallback (~200ms).
curl.exe -s -o NUL --connect-timeout 2 --max-time 3 http://127.0.0.1:%PORT%/api/tools
if %errorlevel% equ 0 goto launch_browser

REM 2) Listening but not answering. If port is held by python/pythonw (e.g. old plain http.server), stop it. Otherwise warn.
powershell -nologo -noprofile -command "$c = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; if ($c) { $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue; if ($p -and $p.ProcessName -in @('python','pythonw')) { Stop-Process -Id $p.Id -Force } elseif ($p) { exit 3 } }; exit 0"
if %errorlevel% equ 3 (
    powershell -nologo -noprofile -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Port %PORT% is held by a non-Python process. Close it then retry.', 'PFD Launcher')" >nul 2>&1
    exit /b 1
)

REM 3) Port free (or freed). Start our server detached (pythonw = no console window).
REM    Probe with `where` first so we can fall back to python and warn if neither exists.
:start_server
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" /min pythonw "%DIR%serve.py"
    goto server_started
)
where python >nul 2>&1
if %errorlevel% equ 0 (
    start "" /min python "%DIR%serve.py"
    goto server_started
)
powershell -nologo -noprofile -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Python が見つかりません. python.org からインストールして PATH に追加してください.', 'PFD Launcher')" >nul 2>&1
exit /b 1

:server_started
powershell -nologo -noprofile -command "Start-Sleep -Milliseconds 800" >nul 2>&1

:launch_browser
REM Startup-only mode: server is up, do NOT open the window (e.g. boot auto-start).
if /i "%~1"=="server" exit /b 0

REM Hand window control to panel.ps1 — docks to the right edge, pins always-on-top,
REM and toggles (open if closed / close if already open).
powershell -nologo -noprofile -ExecutionPolicy Bypass -File "%DIR%panel.ps1" -Action toggle
exit /b 0
