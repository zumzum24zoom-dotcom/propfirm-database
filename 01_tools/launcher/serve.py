"""PFD Launcher server.

Serves the repository root over HTTP and exposes a tiny JSON API for tools.json
so the launcher UI can add/edit/delete tools without a browser file picker.
"""
from __future__ import annotations

import http.server
import json
import os
import socketserver
import subprocess
import sys
import hashlib
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PORT = 8765
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TOOLS_JSON = HERE / "tools.json"

# --- Clipboard history (text + images) -------------------------------------
# clip-watcher.ps1 streams clipboard changes; we keep the most recent CLIP_MAX
# entries in memory. Images are PNG files under CLIP_DIR (evicted with the entry).
CLIP_DIR = Path(os.environ.get("LOCALAPPDATA", str(HERE))) / "PFDLauncher" / "clip"
CLIP_MAX = 50
_clip_lock = threading.Lock()
_clip_items: list[dict] = []   # oldest -> newest
_clip_seq = 0                  # monotonic id counter


def _start_clip_watcher() -> None:
    script = HERE / "clip-watcher.ps1"
    if not script.exists():
        return
    try:
        CLIP_DIR.mkdir(parents=True, exist_ok=True)
        for f in CLIP_DIR.glob("*.png"):   # clear orphans from a previous run
            try:
                f.unlink()
            except OSError:
                pass
        proc = subprocess.Popen(
            ["powershell", "-nologo", "-noprofile", "-sta", "-ExecutionPolicy", "Bypass",
             "-File", str(script), "-ImageDir", str(CLIP_DIR)],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return

    def reader() -> None:
        global _clip_seq
        for line in proc.stdout:                # type: ignore[union-attr]
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            kind = obj.get("type")
            if kind == "text":
                entry = {"type": "text", "text": obj.get("text", ""), "ts": time.time()}
            elif kind == "image":
                entry = {"type": "image", "file": obj.get("file"),
                         "w": obj.get("w"), "h": obj.get("h"), "ts": time.time()}
                try:
                    entry["hash"] = hashlib.md5(Path(entry["file"]).read_bytes()).hexdigest()
                except Exception:
                    entry["hash"] = None
            else:
                continue
            with _clip_lock:
                # Drop consecutive duplicates. Windows cloud-clipboard often re-sets
                # the same content several times, bumping the sequence number each
                # time; collapse those into one history entry.
                last = _clip_items[-1] if _clip_items else None
                if last and last["type"] == entry["type"]:
                    if entry["type"] == "text" and last.get("text") == entry.get("text"):
                        continue
                    # Image: dedup by content hash. Cloud-clipboard re-roams the same
                    # image repeatedly (seconds apart), so a time window isn't enough.
                    if (entry["type"] == "image" and entry.get("hash")
                            and last.get("hash") == entry.get("hash")):
                        if entry.get("file"):
                            try:
                                os.remove(entry["file"])
                            except OSError:
                                pass
                        continue
                _clip_seq += 1
                entry["id"] = str(_clip_seq)
                _clip_items.append(entry)
                while len(_clip_items) > CLIP_MAX:
                    old = _clip_items.pop(0)
                    if old.get("type") == "image" and old.get("file"):
                        try:
                            os.remove(old["file"])
                        except OSError:
                            pass

    threading.Thread(target=reader, daemon=True).start()


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

    def do_GET(self):
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
        if self.path.startswith("/api/clipboard/img/"):
            self._handle_clip_img(self.path.rsplit("/", 1)[-1].split("?")[0])
            return
        if self.path.startswith("/api/clipboard"):
            self._handle_clip_list()
            return
        return super().do_GET()

    def _handle_clip_list(self) -> None:
        with _clip_lock:
            items = []
            for e in reversed(_clip_items):
                if e["type"] == "text":
                    t = e.get("text", "")
                    items.append({"id": e["id"], "type": "text", "ts": e["ts"],
                                  "preview": t[:400], "len": len(t)})
                else:
                    items.append({"id": e["id"], "type": "image", "ts": e["ts"],
                                  "w": e.get("w"), "h": e.get("h")})
        self._json(200, {"ok": True, "items": items})

    def _handle_clip_img(self, cid: str) -> None:
        with _clip_lock:
            e = next((x for x in _clip_items if x["id"] == cid and x["type"] == "image"), None)
            path = e.get("file") if e else None
        if not path or not os.path.isfile(path):
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            blob = Path(path).read_bytes()
        except OSError:
            self._json(404, {"ok": False, "error": "unreadable"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(blob)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(blob)

    def _handle_browse(self):
        qs = parse_qs(urlparse(self.path).query)
        kind = (qs.get("kind", ["html"])[0] or "html").lower()

        if kind == "app":
            # .exe / .lnk picker. Chrome/Edge "installed apps" (PWAs) drop a .lnk
            # shortcut into the Start Menu, so default there for one-click discovery.
            start_menu = os.path.join(
                os.environ.get("APPDATA", ""),
                "Microsoft", "Windows", "Start Menu", "Programs",
            ).replace("'", "''")
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$f = New-Object System.Windows.Forms.OpenFileDialog; "
                f"$f.InitialDirectory = '{start_menu}'; "
                "$f.Filter = 'アプリ・ショートカット|*.exe;*.lnk|All files|*.*'; "
                "$f.Title = 'アプリ(.exe)またはショートカット(.lnk)を選択'; "
                "$f.Multiselect = $false; "
                "if ($f.ShowDialog() -eq 'OK') { Write-Output $f.FileName }"
            )
        else:
            root_str = str(REPO_ROOT).replace("'", "''")
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$f = New-Object System.Windows.Forms.OpenFileDialog; "
                f"$f.InitialDirectory = '{root_str}'; "
                "$f.Filter = 'HTML files|*.html;*.htm|All files|*.*'; "
                "$f.Title = 'ツールHTMLを選択'; "
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

            if kind == "app":
                # Apps live anywhere on disk — store the absolute path verbatim.
                self._json(200, {
                    "ok": True,
                    "path": str(sel_path),
                    "name": sel_path.stem,
                    "type": "app",
                })
                return

            try:
                rel = sel_path.relative_to(REPO_ROOT)
                web_path = "/" + str(rel).replace("\\", "/")
                self._json(200, {"ok": True, "path": web_path, "name": sel_path.stem, "type": "web"})
            except ValueError:
                self._json(200, {
                    "ok": False,
                    "error": "リポジトリ外のファイルは登録できません",
                    "absolute": str(sel_path),
                })
        except Exception as e:
            self._json(500, {"ok": False, "error": str(e)})

    def _handle_launch(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw)
            target = (data.get("path") or "").strip()
            p = Path(target)
            if not target or not p.is_absolute() or not p.is_file():
                raise ValueError("存在する絶対パスのファイルを指定してください")
            # Server binds 127.0.0.1 only, so this is reachable from localhost alone.
            os.startfile(str(p))  # type: ignore[attr-defined]  # Windows: handles .exe/.lnk
            self._json(200, {"ok": True})
        except Exception as e:
            self._json(400, {"ok": False, "error": str(e)})

    def _handle_clip_use(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            cid = str(json.loads(raw).get("id", ""))
            with _clip_lock:
                e = next((x for x in _clip_items if x["id"] == cid), None)
            if not e:
                raise ValueError("not found")
            if e["type"] == "text":
                tf = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
                tf.write(e.get("text", ""))
                tf.close()
                safe = tf.name.replace("'", "''")
                ps = f"Set-Clipboard -Value (Get-Content -Raw -Encoding UTF8 -LiteralPath '{safe}')"
                subprocess.run(["powershell", "-nologo", "-noprofile", "-sta", "-command", ps],
                               capture_output=True, timeout=10)
                try:
                    os.remove(tf.name)
                except OSError:
                    pass
            else:
                p = str(e.get("file", "")).replace("'", "''")
                ps = ("Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
                      f"[System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile('{p}'))")
                subprocess.run(["powershell", "-nologo", "-noprofile", "-sta", "-command", ps],
                               capture_output=True, timeout=10)
            self._json(200, {"ok": True})
        except Exception as exc:
            self._json(400, {"ok": False, "error": str(exc)})

    def _handle_clip_clear(self) -> None:
        with _clip_lock:
            for e in _clip_items:
                if e["type"] == "image" and e.get("file"):
                    try:
                        os.remove(e["file"])
                    except OSError:
                        pass
            _clip_items.clear()
        self._json(200, {"ok": True})

    def do_POST(self):
        if self.path == "/api/launch":
            self._handle_launch()
            return
        if self.path == "/api/clipboard/use":
            self._handle_clip_use()
            return
        if self.path == "/api/clipboard/clear":
            self._handle_clip_clear()
            return
        if self.path == "/api/tools":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                data = json.loads(raw)
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
        self._json(404, {"ok": False, "error": "not found"})

    def log_message(self, *args, **kwargs):
        pass


def main() -> int:
    _start_clip_watcher()
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
