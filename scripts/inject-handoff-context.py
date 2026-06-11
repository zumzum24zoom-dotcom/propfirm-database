#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SessionStart hook: 02_docs/HANDOFF.md（現在地）を additionalContext として自動注入する。

起動時に毎回手動でReadする手間・読み忘れをなくすための仕組み。
PROJECT_MAP.md（構造の正本）は対象外 — 構造調査が必要なタスクの時だけ
Claudeが判断して読めばよく、毎回の固定コストにしない。

入力: stdin に Claude Code から JSON（session_id, cwd 等）
出力: stdout に JSON {hookSpecificOutput: {hookEventName, additionalContext}}
"""
import json
import os
import sys


def main():
    try:
        sys.stdin.read()
    except Exception:
        pass

    repo_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    handoff_path = os.path.join(repo_root, "02_docs", "HANDOFF.md")

    try:
        with open(handoff_path, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return 0

    out = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "# [自動注入] 02_docs/HANDOFF.md（現在地）\n\n" + content,
        }
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
