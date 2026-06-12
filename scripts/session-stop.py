#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SessionStop hook: セッション終了時に未コミット変更を自動コミットし、
HANDOFF.md の最終更新日が今日でなければ警告を追記する。

目的: 作業しっぱなしでプッシュ忘れ・HANDOFF更新忘れを防ぐ。
     HANDOFF の中身は AI が書く必要があるため、このスクリプトは
     「日付の古さ検知＋自動コミット」のみを担当する。
"""
import json
import os
import re
import subprocess
import sys
from datetime import date


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def main():
    try:
        sys.stdin.read()
    except Exception:
        pass

    repo_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    handoff_path = os.path.join(repo_root, "02_docs", "HANDOFF.md")
    today = date.today().strftime("%Y-%m-%d")

    # HANDOFF.md の更新日チェック
    warning = ""
    try:
        with open(handoff_path, encoding="utf-8") as f:
            content = f.read()
        m = re.search(r"最終更新:\s*(\d{4}-\d{2}-\d{2})", content)
        if m and m.group(1) != today:
            warning = f"\n> ⚠ SessionStop自動記録({today}): HANDOFF.md が未更新です。次回セッション開始時に /handoff を実行してください。\n"
            with open(handoff_path, "a", encoding="utf-8") as f:
                f.write(warning)
    except Exception:
        pass

    # 未コミット変更を自動コミット
    status = run(["git", "status", "--porcelain"], cwd=repo_root)
    if status.stdout.strip():
        run(["git", "add", "-A"], cwd=repo_root)
        msg = f"chore: SessionStop自動コミット ({today})"
        if warning:
            msg += " [HANDOFF未更新]"
        run(["git", "commit", "-m", msg], cwd=repo_root)
        run(["git", "push", "-u", "origin", "HEAD"], cwd=repo_root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
