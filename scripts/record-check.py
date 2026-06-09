#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stop hook: 作業終了時に「記録の更新もれ」を検知して Claude に通知する。

検出ルール（lightweight・誤検知より見逃し防止優先）:
- レイアウト変更したが themes/pfd/layouts/_README.md 未更新
- データ構造 (data/firms data/plans) 変更したが該当 _README.md 未更新
- フォルダ/ファイル構成変更したが PROJECT_MAP.md 未更新
- 5ファイル以上変更したが 02_docs/HANDOFF.md 未更新
- Page Maker (MASTER_DEFS) を触ったが 02_docs/page-maker-v11-analysis.md 未更新

検知した場合は decision: block で Claude に更新を促す。
何もなければ silent exit 0。

入力: stdin に Claude Code から JSON（session_id, cwd 等）
出力: stdout に JSON {decision, reason} または何も出さない
"""
import hashlib
import json
import os
import subprocess
import sys

# 承認済みリマインダーのキャッシュ。同一の (ファイル, リマインダー文) を
# 一度承認したらそのセッション内では再通知しない。
CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    ".claude",
    "cache",
    "record-check-acknowledged.json",
)


def load_ack_cache():
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_ack_cache(acked):
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted(acked), f, ensure_ascii=False)
    except Exception:
        pass


def remind_key(files, reminder_text):
    """承認スコープの一意キー: 関連ファイルのfingerprint + リマインダー本文。
    関連ファイルが変わらない限り再通知しない。"""
    files_str = "|".join(sorted(files))
    return hashlib.sha256((files_str + "::" + reminder_text).encode("utf-8")).hexdigest()[:16]


def git(*args):
    try:
        r = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        # NOTE: .strip() は使わない。git status --porcelain の行頭スペース（unstaged-only等）が消えて
        # line[3:] のスライスが1文字ズレるバグの原因になる。末尾改行のみ除去。
        return r.stdout.rstrip("\n")
    except Exception:
        return ""


def get_changed_files():
    """このセッションで触られたファイル一覧（unstaged + staged + untracked）"""
    files = set()
    for line in git("status", "--porcelain").splitlines():
        # フォーマット: "XY path" / "XY path -> newpath"
        if len(line) < 4:
            continue
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        if path:
            files.add(path.replace("\\", "/"))
    return files


def main():
    # stdin を読むが内容は使わない（将来拡張用）
    try:
        sys.stdin.read()
    except Exception:
        pass

    files = get_changed_files()
    if not files:
        return 0

    reminders = []

    # ─── レイアウト変更 vs layouts/_README ───
    layout_changed = any(f.startswith("themes/pfd/layouts/") and f.endswith(".html") for f in files)
    layout_readme = "themes/pfd/layouts/_README.md" in files
    if layout_changed and not layout_readme:
        reminders.append("layouts/*.html を変更 → themes/pfd/layouts/_README.md の対応表を確認・更新")

    # ─── データ構造変更 vs data/_README ───
    firms_data_changed = any(f.startswith("data/firms/") and f.endswith(".json") for f in files)
    firms_readme = "data/firms/_README.md" in files
    # スキーマ的な変更があったか自動判定は難しいので、スロット/構造を触った疑いがあるときだけ通知
    # ここではPage Maker を触ったときに firms/plans の整合を確認するよう促す
    page_maker_changed = any("page-maker" in f for f in files)
    if page_maker_changed:
        if not firms_readme:
            reminders.append("Page Maker 変更 → data/firms/_README.md / data/plans/_README.md のスロット定義整合を確認")
        if "02_docs/page-maker-v11-analysis.md" not in files:
            reminders.append("Page Maker 変更 → 02_docs/page-maker-v11-analysis.md の更新検討（スロット仕様変更時のみ）")

    # ─── 構成変更 vs PROJECT_MAP ───
    structural_signals = [
        f for f in files
        if f.endswith("_README.md")
        or (f.endswith("/") )
        or f in {"hugo.yaml", "netlify.toml"}
    ]
    # 新規フォルダ追加 = 新しい _README が増えた、または top-level に何か増えた
    new_top_level = [
        f for f in files
        if "/" in f and f.split("/")[0] not in {
            "01_tools", "02_docs", "03_intake", "99_chat-tree",
            "archetypes", "content", "data", "scripts", "static",
            "themes", "public", "zz_notes",
            ".claude", ".claudian", ".git", ".github", ".vscode", ".netlify",
        }
    ]
    if (structural_signals or new_top_level) and "PROJECT_MAP.md" not in files:
        reminders.append("構成ファイル/_README を変更 → PROJECT_MAP.md への反映を確認")

    # ─── 大量変更 vs HANDOFF ───
    significant = [f for f in files if not f.startswith(("99_chat-tree/", ".claude/", "public/"))]
    if len(significant) >= 5 and "02_docs/HANDOFF.md" not in files:
        reminders.append(f"{len(significant)}件のファイル変更 → 02_docs/HANDOFF.md に進捗・設計判断を記録")

    # ─── CLAUDE.md 変更時の自己整合チェック ───
    if "CLAUDE.md" in files and "PROJECT_MAP.md" not in files:
        # CLAUDE.md 触ってるなら構造の話が多い。MAP も確認すべきケースが多い
        pass  # 過剰検知になるので無効化

    if not reminders:
        return 0

    # 既に承認済みのリマインダーは除外
    acked = load_ack_cache()
    new_reminders = []
    new_keys = []
    for r in reminders:
        key = remind_key(files, r)
        if key not in acked:
            new_reminders.append(r)
            new_keys.append(key)

    if not new_reminders:
        return 0

    # この通知を出した時点でキャッシュに記録（次ターンでは再通知しない）
    save_ack_cache(acked | set(new_keys))

    msg_lines = [
        "【記録チェック】次の更新もれを確認してください:",
        *[f"  ・ {r}" for r in new_reminders],
        "",
        "更新が不要な場合（軽微な修正・既に反映済み等）は理由を述べてターンを終えてOK。",
        "更新が必要な場合は実施してから終了してください。",
        "",
        "（このリマインダーは同一の変更について再通知されません）",
    ]
    msg = "\n".join(msg_lines)

    out = {"decision": "block", "reason": msg}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
