# PFD Launcher — sidebar window controller.
#   -Action toggle (default): open if closed, close if already open
#   -Action open  : ensure the docked, always-on-top panel is shown & focused
#   -Action close : close the panel window (server keeps running)
#
# Docks a Chrome/Edge --app window to the right screen edge (work area, so it
# never covers the taskbar), full height, narrow width, pinned always-on-top.
param([string]$Action = 'toggle')

$ErrorActionPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Windows.Forms | Out-Null

$PORT  = 8765
$URL   = "http://127.0.0.1:$PORT/01_tools/launcher/"
$TITLE = 'PFD Launcher'
$WIDTH = 360
$UDIR  = Join-Path $env:LOCALAPPDATA 'PFDLauncher\edge-profile'

# --- Win32 interop: find window by title, move/size, set topmost, close ---
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class PfdWin {
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
  [DllImport("user32.dll")] public static extern IntPtr SendMessageTimeout(IntPtr h, uint msg, IntPtr w, IntPtr l, uint flags, uint timeout, out IntPtr res);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
}
"@ | Out-Null

function Find-PanelWindow {
  # Find the panel window whether shown or hidden (we hide instead of closing,
  # so a previous instance may be sitting hidden and ready to re-show instantly).
  $script:found = [IntPtr]::Zero
  $cb = [PfdWin+EnumProc] {
    param($h, $p)
    $sb = New-Object System.Text.StringBuilder 256
    [PfdWin]::GetWindowText($h, $sb, 256) | Out-Null
    if ($sb.ToString().StartsWith($TITLE)) { $script:found = $h; return $false }
    return $true
  }
  [PfdWin]::EnumWindows($cb, [IntPtr]::Zero) | Out-Null
  return $script:found
}

$SW_HIDE = 0
$SW_SHOW = 5

function Dock-And-Pin([IntPtr]$h) {
  $wa = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
  $HWND_TOPMOST   = [IntPtr](-1)
  $SWP_SHOWWINDOW = 0x0040
  [PfdWin]::ShowWindow($h, $SW_SHOW) | Out-Null
  [PfdWin]::SetWindowPos($h, $HWND_TOPMOST, ($wa.Right - $WIDTH), $wa.Top, $WIDTH, $wa.Height, $SWP_SHOWWINDOW) | Out-Null
}

$hwnd = Find-PanelWindow

if ($Action -eq 'toggle') {
  # Hide instead of close, so the next open is instant (no browser relaunch).
  if ($hwnd -ne [IntPtr]::Zero -and [PfdWin]::IsWindowVisible($hwnd)) { $Action = 'close' } else { $Action = 'open' }
}

if ($Action -eq 'close') {
  if ($hwnd -ne [IntPtr]::Zero) {
    [PfdWin]::ShowWindow($hwnd, $SW_HIDE) | Out-Null
  }
  return
}

# --- open ---
if ($hwnd -ne [IntPtr]::Zero) {
  Dock-And-Pin $hwnd
  [PfdWin]::SetForegroundWindow($hwnd) | Out-Null
  return
}

# Pre-create sentinel files so Edge/Chrome skip the first-run welcome flow.
if (-not (Test-Path $UDIR)) { New-Item -ItemType Directory -Path $UDIR -Force | Out-Null }
$firstRun = Join-Path $UDIR 'First Run'
if (-not (Test-Path $firstRun)) { New-Item -ItemType File -Path $firstRun -Force | Out-Null }
$defDir = Join-Path $UDIR 'Default'
if (-not (Test-Path $defDir)) { New-Item -ItemType Directory -Path $defDir -Force | Out-Null }
$prefs = Join-Path $defDir 'Preferences'
if (-not (Test-Path $prefs)) {
  '{"profile":{"exit_type":"Normal","exited_cleanly":true},"browser":{"has_seen_welcome_page":true,"show_home_button":false}}' |
    Out-File -FilePath $prefs -Encoding ascii
}

# Find a browser: Chrome first (matches prior behaviour), then Edge.
$browser = $null
foreach ($c in @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
)) { if (Test-Path $c) { $browser = $c; break } }

$wa = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$x  = $wa.Right - $WIDTH

if ($browser) {
  $flags = @(
    "--app=$URL",
    "--user-data-dir=$UDIR",
    "--window-position=$x,$($wa.Top)",
    "--window-size=$WIDTH,$($wa.Height)",
    "--no-first-run", "--no-default-browser-check", "--no-service-autorun", "--disable-sync",
    "--disable-features=msEdgeFirstRunExperience,EdgeWelcomeEnabled,WelcomeExperienceEnabled,msUndersideButton"
  )
  Start-Process -FilePath $browser -ArgumentList $flags
} else {
  Start-Process $URL   # last resort: default browser, no docking possible
  return
}

# Wait for the window to appear, then dock + pin.
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Milliseconds 100
  $hwnd = Find-PanelWindow
  if ($hwnd -ne [IntPtr]::Zero) { break }
}
if ($hwnd -ne [IntPtr]::Zero) { Dock-And-Pin $hwnd }
