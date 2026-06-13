"""PostToolUse フック: ランチャーの Python ファイル(01_tools/launcher/*.py)が
Claude の Edit/Write で変更されたら、自動でランチャー(agent.py)を再起動する。

仕組み: フックは stdin に tool_input(file_path 含む)の JSON を受け取る。対象ファイル
でなければ何もしない（毎回の編集で走るが no-op）。対象なら旧プロセスを停止して再起動。

注意: これは「Claude が編集したとき」に発火する。VS Code で手動保存した場合は
Claude のフック対象外なので発火しない（その場合は手動で再起動 or 私に頼む）。
"""
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    raw = ""
    try:
        raw = sys.stdin.read()
    except Exception:
        pass
    fp = ""
    try:
        import json
        data = json.loads(raw) if raw.strip() else {}
        fp = ((data.get("tool_input") or {}).get("file_path") or "")
    except Exception:
        fp = ""

    p = fp.replace("\\", "/").lower()
    if not ("01_tools/launcher/" in p and p.endswith(".py")):
        return 0  # 対象外: 何もしない

    agent = Path(__file__).resolve().parents[1] / "01_tools" / "launcher" / "agent.py"

    # 旧 agent を停止（pythonw で agent.py を実行中のもの）
    kill = (
        "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | "
        "Where-Object { $_.CommandLine -like '*agent.py*' } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", kill],
                       capture_output=True, timeout=10)
    except Exception:
        pass

    # 再起動（デタッチ。agent 側の多重起動ガードもあるので安全）
    try:
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(["pythonw", str(agent)], creationflags=flags)
        print(f"🔁 launcher agent を再起動しました（編集: {os.path.basename(fp)}）")
    except Exception as e:
        print(f"⚠ ランチャー再起動に失敗: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
