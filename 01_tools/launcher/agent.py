"""PFD Launcher Agent — persistent background process.

Replaces serve.py. Runs the launcher HTTP server (tools API, clipboard API,
app-launch API) plus a Win32 message loop that provides:
  - clipboard history capture (text + images)
  - a global hotkey (Ctrl+Alt+L) to show/hide the sidebar window
  - always-on-top toggle for the sidebar window

Start at logon via Task Scheduler (see register-startup.ps1).
"""
from __future__ import annotations

import ctypes
import datetime
import hashlib
import http.server
import json
import os
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

import win32api
import win32con
import win32gui

import clipboard_store
import wincontrol

PORT = 8765
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TOOLS_JSON = HERE / "tools.json"
LOG_FILE = HERE / "agent.log"
SIDEBAR_TITLE = "PFD Launcher"
SIDEBAR_URL = f"http://localhost:{PORT}/01_tools/launcher/"
SIDEBAR_WIDTH = 360
SIDEBAR_MARGIN_BOTTOM = 48  # rough allowance for taskbar

WM_CLIPBOARDUPDATE = 0x031D
HOTKEY_TOGGLE = 1
HOTKEY_MODS = win32con.MOD_NOREPEAT  # no Ctrl/Alt/Shift - Insert key alone
HOTKEY_VK = win32con.VK_INSERT

_last_written: tuple[str, str] | None = None  # (kind, hash/text) of clipboard we wrote ourselves


def _log(msg: str) -> None:
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}\n"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length))

    # -- GET --------------------------------------------------------------
    def do_GET(self):
        if self.path.startswith("/api/ping"):
            self._json(200, {"ok": True})
            return
        if self.path.startswith("/api/tools"):
            try:
                data = json.loads(TOOLS_JSON.read_text(encoding="utf-8"))
                self._json(200, data)
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
            return
        if self.path.startswith("/api/browse"):
            self._handle_browse()
            return
        if self.path.startswith("/api/apps"):
            self._handle_apps()
            return
        if self.path.startswith("/api/clipboard/image/"):
            self._handle_clipboard_image()
            return
        if self.path.startswith("/api/clipboard"):
            items = clipboard_store.list_items()
            self._json(200, {"items": items})
            return
        return super().do_GET()

    def _handle_browse(self):
        only_html = "/api/browse/html" in self.path or self.path.endswith("html=1")
        filt = "HTML files|*.html;*.htm|All files|*.*" if only_html else "All files|*.*"
        root_str = str(REPO_ROOT).replace("'", "''")
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$f = New-Object System.Windows.Forms.OpenFileDialog; "
            f"$f.InitialDirectory = '{root_str}'; "
            f"$f.Filter = '{filt}'; "
            "$f.Title = 'ファイルを選択'; "
            "$f.Multiselect = $false; "
            "if ($f.ShowDialog() -eq 'OK') { Write-Output $f.FileName }"
        )
        try:
            result = subprocess.run(
                ["powershell", "-nologo", "-noprofile", "-sta", "-command", ps],
                capture_output=True, text=True, timeout=300,
            )
            selected = (result.stdout or "").strip()
            if not selected:
                self._json(200, {"ok": True, "cancelled": True})
                return
            sel_path = Path(selected).resolve()
            try:
                rel = sel_path.relative_to(REPO_ROOT)
                web_path = "/" + str(rel).replace("\\", "/")
                self._json(200, {"ok": True, "path": web_path, "name": sel_path.stem, "absolute": str(sel_path)})
            except ValueError:
                # Outside repo: fine for exe/file type tools, return absolute path
                self._json(200, {"ok": True, "path": str(sel_path), "name": sel_path.stem, "absolute": str(sel_path)})
        except Exception as e:
            self._json(500, {"ok": False, "error": str(e)})

    def _handle_apps(self):
        ps = "Get-StartApps | ConvertTo-Json -Compress"
        try:
            result = subprocess.run(
                ["powershell", "-nologo", "-noprofile", "-command", ps],
                capture_output=True, text=True, timeout=30,
            )
            raw = json.loads(result.stdout or "[]")
            if isinstance(raw, dict):
                raw = [raw]
            apps = [{"name": a.get("Name", ""), "appid": a.get("AppID", "")} for a in raw]
            apps.sort(key=lambda a: a["name"].lower())
            self._json(200, {"ok": True, "apps": apps})
        except Exception as e:
            self._json(500, {"ok": False, "error": str(e)})

    def _handle_clipboard_image(self):
        filename = self.path.rsplit("/", 1)[-1].split("?", 1)[0]
        if "/" in filename or "\\" in filename or not filename.endswith(".png"):
            self._json(404, {"ok": False, "error": "not found"})
            return
        path = clipboard_store.IMG_DIR / filename
        if not path.is_file():
            self._json(404, {"ok": False, "error": "not found"})
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    # -- POST -------------------------------------------------------------
    def do_POST(self):
        if self.path == "/api/tools":
            try:
                data = self._read_json()
                if not isinstance(data, dict) or "tools" not in data:
                    raise ValueError("payload must be an object containing 'tools'")
                TOOLS_JSON.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                self._json(200, {"ok": True})
            except Exception as e:
                self._json(400, {"ok": False, "error": str(e)})
            return
        if self.path == "/api/launch":
            self._handle_launch()
            return
        if self.path == "/api/open-url":
            self._handle_open_url()
            return
        if self.path == "/api/clipboard/restore":
            self._handle_clipboard_restore()
            return
        if self.path == "/api/clipboard/delete":
            self._handle_clipboard_delete()
            return
        if self.path == "/api/clipboard/clear":
            clipboard_store.clear_all()
            self._json(200, {"ok": True})
            return
        if self.path == "/api/window/toggle":
            state = toggle_sidebar()
            self._json(200, {"ok": True, "state": state})
            return
        if self.path == "/api/window/topmost":
            try:
                data = self._read_json()
                hwnd = wincontrol.find_sidebar_window(SIDEBAR_TITLE)
                if not hwnd:
                    self._json(404, {"ok": False, "error": "sidebar window not found"})
                    return
                wincontrol.set_topmost(hwnd, bool(data.get("on")))
                self._json(200, {"ok": True, "topmost": bool(data.get("on"))})
            except Exception as e:
                self._json(400, {"ok": False, "error": str(e)})
            return
        self._json(404, {"ok": False, "error": "not found"})

    def _handle_launch(self):
        try:
            data = self._read_json()
            path = data.get("path", "")
            kind = data.get("type", "exe")
            if not path:
                raise ValueError("path is required")
            target = f"shell:AppsFolder\\{path}" if kind == "pwa" else path
            os.startfile(target)
            self._json(200, {"ok": True})
        except Exception as e:
            self._json(400, {"ok": False, "error": str(e)})

    def _handle_open_url(self):
        try:
            data = self._read_json()
            url = data.get("url")
            x = int(data.get("x", 0))
            y = int(data.get("y", 0))
            w = int(data.get("w", 0))
            h = int(data.get("h", 0))
            if not url or w <= 0 or h <= 0:
                raise ValueError("url, w, h are required")
            # 相対パスはサーバルートから解釈
            if url.startswith("/"):
                url = f"http://localhost:{PORT}{url}"
            launch_app_window(url, x, y, w, h)
            self._json(200, {"ok": True})
        except Exception as e:
            self._json(400, {"ok": False, "error": str(e)})

    def _handle_clipboard_restore(self):
        global _last_written
        try:
            data = self._read_json()
            item = clipboard_store.get_item(int(data["id"]))
            if not item:
                self._json(404, {"ok": False, "error": "not found"})
                return
            if item["type"] == "text":
                wincontrol.write_text(item["content"])
                _last_written = ("text", item["content"])
            else:
                png = (clipboard_store.IMG_DIR / item["image_file"]).read_bytes()
                wincontrol.write_image(png)
                _last_written = ("image", hashlib.sha1(png).hexdigest())
            self._json(200, {"ok": True})
        except Exception as e:
            self._json(400, {"ok": False, "error": str(e)})

    def _handle_clipboard_delete(self):
        try:
            data = self._read_json()
            clipboard_store.delete_item(int(data["id"]))
            self._json(200, {"ok": True})
        except Exception as e:
            self._json(400, {"ok": False, "error": str(e)})

    def log_message(self, *args, **kwargs):
        pass


def run_server() -> None:
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()


# ---------------------------------------------------------------------------
# Sidebar window control
# ---------------------------------------------------------------------------

def _ensure_profile(udir: Path) -> None:
    udir.mkdir(parents=True, exist_ok=True)
    (udir / "First Run").touch(exist_ok=True)
    default = udir / "Default"
    default.mkdir(exist_ok=True)
    prefs = default / "Preferences"
    if not prefs.exists():
        prefs.write_text(
            '{"profile":{"exit_type":"Normal","exited_cleanly":true},'
            '"browser":{"has_seen_welcome_page":true,"show_home_button":false}}',
            encoding="utf-8",
        )


def launch_sidebar() -> None:
    candidates = [
        Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
    ]
    browser = next((c for c in candidates if c.is_file()), None)
    if not browser:
        os.startfile(SIDEBAR_URL)
        return
    udir = Path(os.environ["LOCALAPPDATA"]) / "PFDLauncher" / "edge-profile"
    _ensure_profile(udir)
    screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    pos_x = screen_w - SIDEBAR_WIDTH
    height = screen_h - SIDEBAR_MARGIN_BOTTOM
    flags = [
        str(browser),
        f"--app={SIDEBAR_URL}",
        f"--window-size={SIDEBAR_WIDTH},{height}",
        f"--window-position={pos_x},0",
        f"--user-data-dir={udir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--no-service-autorun",
        "--disable-sync",
    ]
    subprocess.Popen(flags)
    threading.Thread(
        target=_dock_when_ready, args=(pos_x, 0, SIDEBAR_WIDTH, height), daemon=True
    ).start()


def launch_app_window(url: str, x: int, y: int, w: int, h: int) -> None:
    """ツール用Chromeウィンドウを指定位置・サイズで起動。

    window.open がChrome --appモード下では features を無視するため、
    agent.py側からChromeを直接subprocessで起動する。
    """
    candidates = [
        Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
    ]
    browser = next((c for c in candidates if c.is_file()), None)
    if not browser:
        os.startfile(url)
        return
    udir = Path(os.environ["LOCALAPPDATA"]) / "PFDLauncher" / "tool-profile"
    _ensure_profile(udir)
    flags = [
        str(browser),
        f"--app={url}",
        f"--window-size={w},{h}",
        f"--window-position={x},{y}",
        f"--user-data-dir={udir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--no-service-autorun",
        "--disable-sync",
    ]
    subprocess.Popen(flags)


def _dock_when_ready(x: int, y: int, w: int, h: int) -> None:
    """Edge restores its last window position/size from the profile's
    Preferences file, overriding --window-size/--window-position. Poll for
    the new window and force it back to the docked rect once it appears."""
    for _ in range(50):
        hwnd = wincontrol.find_sidebar_window(SIDEBAR_TITLE)
        if hwnd:
            wincontrol.set_rect(hwnd, x, y, w, h)
            return
        time.sleep(0.1)


def toggle_sidebar() -> str:
    hwnd = wincontrol.find_sidebar_window(SIDEBAR_TITLE)
    if hwnd:
        return wincontrol.toggle_visibility(hwnd)
    launch_sidebar()
    return "launched"


# ---------------------------------------------------------------------------
# Clipboard capture
# ---------------------------------------------------------------------------

def on_clipboard_update() -> None:
    global _last_written
    try:
        kind, value = wincontrol.read_clipboard()
    except Exception as e:
        _log(f"clipboard read failed: {e}")
        return
    if kind == "text":
        if _last_written == ("text", value):
            _last_written = None
            return
        clipboard_store.add_text(value)
    elif kind == "image":
        h = hashlib.sha1(value).hexdigest()
        if _last_written == ("image", h):
            _last_written = None
            return
        clipboard_store.add_image(value)


# ---------------------------------------------------------------------------
# Win32 message loop (hidden window: hotkey + clipboard listener)
# ---------------------------------------------------------------------------

def _wnd_proc(hwnd, msg, wparam, lparam):
    if msg == win32con.WM_HOTKEY and wparam == HOTKEY_TOGGLE:
        try:
            toggle_sidebar()
        except Exception as e:
            _log(f"toggle_sidebar failed: {e}")
        return 0
    if msg == WM_CLIPBOARDUPDATE:
        on_clipboard_update()
        return 0
    if msg == win32con.WM_DESTROY:
        win32gui.PostQuitMessage(0)
        return 0
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


def run_message_loop() -> None:
    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _wnd_proc
    wc.lpszClassName = "PFDLauncherAgentWnd"
    wc.hInstance = win32api.GetModuleHandle(None)
    class_atom = win32gui.RegisterClass(wc)
    hwnd = win32gui.CreateWindow(
        class_atom, "PFD Launcher Agent", 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None
    )

    if not ctypes.windll.user32.AddClipboardFormatListener(hwnd):
        _log("AddClipboardFormatListener failed")

    try:
        win32gui.RegisterHotKey(hwnd, HOTKEY_TOGGLE, HOTKEY_MODS, HOTKEY_VK)
    except win32gui.error as e:
        _log(f"RegisterHotKey(Insert) failed (already in use?): {e}")

    win32gui.PumpMessages()


def main() -> int:
    _log("agent starting")
    threading.Thread(target=run_server, daemon=True).start()
    run_message_loop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
