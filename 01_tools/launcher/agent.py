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
from ctypes import wintypes
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
MEMO_FILE = HERE / "memo.txt"
LOG_FILE = HERE / "agent.log"

# Firm Dashboard (FD-*) のデータ源。本体ロジックではなく場所の定義に留める。
DATA_DIR = REPO_ROOT / "data"
FIRMS_DIR = DATA_DIR / "firms"
PLANS_DIR = DATA_DIR / "plans"
CONTENT_FIRMS_DIR = REPO_ROOT / "content" / "firms"
PROGRESS_FILE = DATA_DIR / "progress.json"
# 1社1データの編集用正本（page-maker改 が読み書きする）。公開用 firms/ とは別。
FIRMS_EDIT_DIR = DATA_DIR / "firms-edit"

_SLUG_OK = set("abcdefghijklmnopqrstuvwxyz0123456789-_")


def _safe_slug(slug: str) -> str:
    """パストラバーサル防止: 想定文字以外を含む slug は拒否。"""
    slug = (slug or "").strip()
    if not slug or not set(slug) <= _SLUG_OK:
        raise ValueError("invalid slug")
    return slug
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
        if self.path.startswith("/api/memo"):
            try:
                text = MEMO_FILE.read_text(encoding="utf-8") if MEMO_FILE.exists() else ""
            except OSError:
                text = ""
            self._json(200, {"text": text})
            return
        # Firm Dashboard: ファーム一覧＋ランプ判定用の生計測値（FD-04/FD-06）
        if self.path.startswith("/api/firms"):
            try:
                self._json(200, {"firms": scan_firms()})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
            return
        # Firm Dashboard: 進捗の読み取り（FD-05）
        if self.path.startswith("/api/progress"):
            self._json(200, read_progress())
            return
        # page-maker改: 1社の編集用データを読む（?slug=...）
        if self.path.startswith("/api/firm-edit"):
            try:
                from urllib.parse import urlparse, parse_qs
                slug = _safe_slug(parse_qs(urlparse(self.path).query).get("slug", [""])[0])
                fp = FIRMS_EDIT_DIR / f"{slug}.json"
                if not fp.is_file():
                    self._json(404, {"ok": False, "error": f"not found: {slug}"})
                    return
                self._json(200, {"ok": True, "data": json.loads(fp.read_text(encoding="utf-8"))})
            except Exception as e:
                self._json(400, {"ok": False, "error": str(e)})
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
        if self.path == "/api/memo":
            try:
                data = self._read_json()
                MEMO_FILE.write_text(str(data.get("text", "")), encoding="utf-8")
                self._json(200, {"ok": True})
            except Exception as e:
                self._json(400, {"ok": False, "error": str(e)})
            return
        if self.path == "/api/progress":
            # Firm Dashboard: 進捗の保存（FD-05）。1社分 {slug,status,note?} を受けてマージ。
            try:
                data = self._read_json()
                slug = str(data.get("slug", "")).strip()
                if not slug:
                    raise ValueError("slug is required")
                store = read_progress()
                entry = store["firms"].get(slug, {})
                if "status" in data:
                    entry["status"] = str(data["status"])
                if "note" in data:
                    entry["note"] = str(data["note"])
                entry["updated"] = datetime.date.today().isoformat()
                store["firms"][slug] = entry
                write_progress(store)
                self._json(200, {"ok": True, "slug": slug, "entry": entry})
            except Exception as e:
                self._json(400, {"ok": False, "error": str(e)})
            return
        if self.path == "/api/firm-edit":
            # page-maker改: 1社の編集用データを保存。{slug, data} を data/firms-edit/{slug}.json へ。
            try:
                payload = self._read_json()
                slug = _safe_slug(payload.get("slug", ""))
                data = payload.get("data")
                if not isinstance(data, dict):
                    raise ValueError("data must be an object")
                FIRMS_EDIT_DIR.mkdir(parents=True, exist_ok=True)
                (FIRMS_EDIT_DIR / f"{slug}.json").write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                self._json(200, {"ok": True, "slug": slug})
            except Exception as e:
                self._json(400, {"ok": False, "error": str(e)})
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
            pane = data.get("pane", "left")
            if not url:
                raise ValueError("url is required")
            # 相対パスはサーバルートから解釈
            if url.startswith("/"):
                url = f"http://localhost:{PORT}{url}"
            open_tool_pane(url, pane)
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


# ---------------------------------------------------------------------------
# Firm Dashboard data (FD-04/05/06)
# ---------------------------------------------------------------------------
# 方針: サーバーは「生の計測値」だけ返し、点灯しきい値などの解釈はダッシュボード
# 側の config に委ねる（しきい値のハードコードを1箇所に集約しないための分離）。

def scan_firms() -> list[dict]:
    """data/firms/*.json を走査し、各ファームのメタ＋ランプ判定用の生計測値を返す。
    firmFilled=非空フィールド数 / planCount=対応プラン数 / stratBytes=攻略記事サイズ。"""
    out: list[dict] = []
    if not FIRMS_DIR.is_dir():
        return out
    for jp in sorted(FIRMS_DIR.glob("*.json")):
        if jp.name.startswith("_"):
            continue
        try:
            d = json.loads(jp.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        slug = (d.get("slug") or jp.stem).strip()
        name = (d.get("ファーム名") or slug).strip()
        url = (d.get("公式URL") or "").strip()
        filled = sum(
            1 for k, v in d.items()
            if k != "slug" and isinstance(v, str) and v.strip()
        )
        plan_count = sum(1 for _ in PLANS_DIR.glob(f"{slug}--*.json")) if PLANS_DIR.is_dir() else 0
        idx = CONTENT_FIRMS_DIR / slug / "_index.md"
        strat_bytes = idx.stat().st_size if idx.is_file() else 0
        out.append({
            "slug": slug,
            "name": name,
            "url": url,
            "planCount": plan_count,
            "firmFilled": filled,
            "stratBytes": strat_bytes,
        })
    return out


def read_progress() -> dict:
    """progress.json を読む。壊れていても落ちないよう既定形にフォールバック。"""
    base = {"firms": {}}
    try:
        data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("firms"), dict):
            base.update(data)
            base["firms"] = data["firms"]
    except Exception:
        pass
    return base


def write_progress(store: dict) -> None:
    PROGRESS_FILE.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


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


# Tool windows tile into the zone left of the sidebar. We track the window
# currently occupying each pane so that opening a second tool re-tiles both to
# half width (clean side-by-side split) instead of overlapping.
_pane_lock = threading.Lock()
_pane_hwnds: dict[str, int | None] = {"left": None, "right": None}


def _work_zone() -> tuple[int, int, int, int]:
    """The (x, y, w, h) rectangle available to tool windows: the desktop work
    area (taskbar excluded), minus the docked sidebar on the right *only when
    the sidebar is actually visible*. When the sidebar is hidden/closed the
    tool windows expand to fill that freed space (auto-arrange)."""
    rect = wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)  # SPI_GETWORKAREA
    x, y = rect.left, rect.top
    reserve = SIDEBAR_WIDTH if _sidebar_visible() else 0
    w = (rect.right - reserve) - rect.left
    h = rect.bottom - rect.top
    return x, y, w, h


def _sidebar_visible() -> bool:
    hwnd = wincontrol.find_sidebar_window(SIDEBAR_TITLE)
    return bool(hwnd) and win32gui.IsWindowVisible(hwnd)


def retile_panes() -> None:
    """Reposition the live tool windows for the current zone. Called when the
    sidebar is shown/hidden so tools shrink to leave room / expand to fill it."""
    rects = _pane_rects()
    with _pane_lock:
        left_live = _alive(_pane_hwnds["left"])
        right_live = _alive(_pane_hwnds["right"])
        if left_live and right_live:
            wincontrol.set_rect(_pane_hwnds["left"], *rects["left"])
            wincontrol.set_rect(_pane_hwnds["right"], *rects["right"])
        elif left_live:
            wincontrol.set_rect(_pane_hwnds["left"], *rects["full"])
        elif right_live:
            wincontrol.set_rect(_pane_hwnds["right"], *rects["full"])


def _sidebar_watch_loop() -> None:
    """Poll sidebar visibility; when it changes (toggle or close), re-tile the
    tool windows so they fill or yield the sidebar's space automatically."""
    was = None
    while True:
        try:
            vis = _sidebar_visible()
            if was is not None and vis != was:
                retile_panes()
            was = vis
        except Exception as e:
            _log(f"sidebar watch failed: {e}")
        time.sleep(0.4)


def _pane_rects() -> dict[str, tuple[int, int, int, int]]:
    zx, zy, zw, zh = _work_zone()
    half = zw // 2
    return {
        "full": (zx, zy, zw, zh),
        "left": (zx, zy, half, zh),
        "right": (zx + half, zy, zw - half, zh),
    }


def _alive(hwnd: int | None) -> bool:
    return bool(hwnd) and win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)


def _find_browser() -> Path | None:
    candidates = [
        Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
    ]
    return next((c for c in candidates if c.is_file()), None)


def open_tool_pane(url: str, pane: str) -> None:
    """Open a tool window in the given pane ('left'/'right'). If the opposite
    pane already holds a live window, both are tiled to half width for a clean
    split; otherwise the new window gets the full zone.

    window.open is ignored under Chrome --app mode and Chrome ignores
    --window-size once a profile has saved bounds, so we launch Chrome
    directly and force the rect after the window appears.
    """
    pane = "right" if pane == "right" else "left"
    other = "right" if pane == "left" else "left"
    rects = _pane_rects()

    with _pane_lock:
        other_hwnd = _pane_hwnds[other]
        other_live = _alive(other_hwnd)
    if other_live:
        target = rects[pane]
        wincontrol.set_rect(other_hwnd, *rects[other])  # re-tile the existing one
    else:
        target = rects["full"]

    browser = _find_browser()
    if not browser:
        os.startfile(url)
        return
    udir = Path(os.environ["LOCALAPPDATA"]) / "PFDLauncher" / "tool-profile"
    _ensure_profile(udir)
    x, y, w, h = target
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
    before = wincontrol.list_chrome_windows()
    subprocess.Popen(flags)
    threading.Thread(
        target=_adopt_new_window, args=(before, pane, target), daemon=True
    ).start()


def _adopt_new_window(before: set[int], pane: str, target: tuple[int, int, int, int]) -> None:
    """Find the Chrome window that appeared after launch, record it as the
    occupant of `pane`, and force its rect (twice - Chrome may re-apply its
    saved bounds shortly after the window first appears)."""
    for _ in range(60):
        new = wincontrol.list_chrome_windows() - before
        if new:
            hwnd = next(iter(new))
            with _pane_lock:
                _pane_hwnds[pane] = hwnd
            wincontrol.set_rect(hwnd, *target)
            time.sleep(0.25)
            wincontrol.set_rect(hwnd, *target)
            return
        time.sleep(0.1)


def _dock_when_ready(x: int, y: int, w: int, h: int) -> None:
    """Chrome restores its last window position/size from the profile's
    Preferences file, overriding --window-size/--window-position. Poll for
    the new window and slide it in to the docked rect once it appears (so the
    first launch animates the same as a toggle instead of popping)."""
    for _ in range(160):
        hwnd = wincontrol.find_sidebar_window(SIDEBAR_TITLE)
        if hwnd:
            wincontrol.fade_in(hwnd, x, y, w, h)
            return
        time.sleep(0.05)


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
    # Title deliberately does NOT contain "PFD Launcher" so find_sidebar_window
    # (substring match) can never mistake this hidden control window for the
    # Chrome sidebar. It is a non-visible message window (created with no
    # WS_VISIBLE style) used only for the hotkey + clipboard listener.
    hwnd = win32gui.CreateWindow(
        class_atom, "PFDAgentMsgWnd", 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None
    )

    if not ctypes.windll.user32.AddClipboardFormatListener(hwnd):
        _log("AddClipboardFormatListener failed")

    try:
        win32gui.RegisterHotKey(hwnd, HOTKEY_TOGGLE, HOTKEY_MODS, HOTKEY_VK)
    except win32gui.error as e:
        _log(f"RegisterHotKey(Insert) failed (already in use?): {e}")

    win32gui.PumpMessages()


def _already_running() -> bool:
    """True if another agent already answers on PORT. Prevents duplicate
    instances (task-scheduler launch + manual launch) from stacking up - the
    extras can't bind the port or grab the hotkey and only cause confusion."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/ping", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def main() -> int:
    if _already_running():
        _log("another agent already running on port %d; exiting" % PORT)
        return 0
    _log("agent starting")
    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=_sidebar_watch_loop, daemon=True).start()
    run_message_loop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
