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
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PORT = 8765
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TOOLS_JSON = HERE / "tools.json"


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
        return super().do_GET()

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

    def do_POST(self):
        if self.path == "/api/launch":
            self._handle_launch()
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
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
