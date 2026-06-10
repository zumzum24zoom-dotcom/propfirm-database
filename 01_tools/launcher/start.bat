@echo off
setlocal
set PORT=8765
set DIR=%~dp0
set URL=http://localhost:%PORT%/01_tools/launcher/

REM 1) Probe /api/tools — if it returns valid JSON, our serve.py is already up.
powershell -nologo -noprofile -command "try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 1 'http://localhost:%PORT%/api/tools').Content | ConvertFrom-Json | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto launch_browser

REM 2) Not responding properly. If port is held by python/pythonw (e.g. old plain http.server), stop it. Otherwise warn.
powershell -nologo -noprofile -command "$c = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; if ($c) { $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue; if ($p -and $p.ProcessName -in @('python','pythonw')) { Stop-Process -Id $p.Id -Force } elseif ($p) { exit 3 } }; exit 0"
if %errorlevel% equ 3 (
    powershell -nologo -noprofile -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Port %PORT% is held by a non-Python process. Close it then retry.', 'PFD Launcher')" >nul 2>&1
    exit /b 1
)

REM 3) Port free (or freed). Start our server.
start "" /min pythonw "%DIR%serve.py"
powershell -nologo -noprofile -command "Start-Sleep -Milliseconds 800" >nul 2>&1

:launch_browser
set EDGE=
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe

set CHROME=
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe

set UDIR=%LOCALAPPDATA%\PFDLauncher\edge-profile

REM Pre-create sentinel files so Edge/Chrome skip the first-run welcome flow
if not exist "%UDIR%" mkdir "%UDIR%" >nul 2>&1
if not exist "%UDIR%\First Run" type nul > "%UDIR%\First Run"
if not exist "%UDIR%\Default" mkdir "%UDIR%\Default" >nul 2>&1
if not exist "%UDIR%\Default\Preferences" (
    >"%UDIR%\Default\Preferences" echo {"profile":{"exit_type":"Normal","exited_cleanly":true},"browser":{"has_seen_welcome_page":true,"show_home_button":false}}
)

set FLAGS=--app=%URL% --window-size=520,760 --user-data-dir="%UDIR%" --no-first-run --no-default-browser-check --no-service-autorun --disable-sync --disable-features=msEdgeFirstRunExperience,EdgeWelcomeEnabled,WelcomeExperienceEnabled,msUndersideButton

if defined CHROME (
    start "" "%CHROME%" %FLAGS%
    exit /b 0
)
if defined EDGE (
    start "" "%EDGE%" %FLAGS%
    exit /b 0
)

start "" %URL%
