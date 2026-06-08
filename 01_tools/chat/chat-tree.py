#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chat-tree.py — Claude Code セッション(JSONL)を Obsidian 用の
Mermaid ツリー図(Markdown)に変換する。

使い方:
    python 01_tools/chat-tree.py
        → 全セッションを変換し 99_chat-tree/ に出力
    python 01_tools/chat-tree.py <sessionId or jsonlパス>
        → 1セッションだけ変換

仕組み:
    各メッセージは uuid / parentUuid を持つツリー構造。
    人間の発言(チェックポイント)だけに畳み込み、最も近い
    祖先の人間発言へ連結 → 分岐を可視化する。
    各ノードに sessionId を持たせ「resume + 巻き戻し」で再開できる。
"""
import json
import sys
import re
from pathlib import Path

PROJECT_DIR = Path(r"C:/Users/Zumzum/.claude/projects/D--vs-code-propfirm-database")
VAULT_ROOT = Path(r"D:/vs code/propfirm-database")
OUT_DIR = VAULT_ROOT / "99_chat-tree"


def extract_text(content):
    """message.content から人間の発言テキストを取り出す。tool_result は無視。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for x in content:
            if isinstance(x, dict) and x.get("type") == "text":
                parts.append(x.get("text", ""))
            elif isinstance(x, dict) and x.get("type") == "image":
                parts.append("[画像]")
        return " ".join(parts)
    return ""


def is_human(rec):
    """type=user かつ tool_result でない = 人間のチェックポイント発言。"""
    if rec.get("type") != "user" or rec.get("isSidechain"):
        return False
    m = rec.get("message", {})
    c = m.get("content")
    if isinstance(c, str):
        return c.strip() != ""
    if isinstance(c, list):
        return any(isinstance(x, dict) and x.get("type") in ("text", "image") for x in c)
    return False


def load_session(jsonl_path):
    recs = {}        # uuid -> record
    order = []       # uuid を出現順に
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        u = d.get("uuid")
        if not u:
            continue
        recs[u] = d
        order.append(u)
    return recs, order


def nearest_human_ancestor(uuid, recs):
    """uuid から親を遡り、最も近い人間発言の uuid を返す(無ければ None)。"""
    cur = recs.get(uuid, {}).get("parentUuid")
    while cur:
        r = recs.get(cur)
        if r is None:
            return None
        if is_human(r):
            return cur
        cur = r.get("parentUuid")
    return None


def sanitize(text, limit=40):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[:limit] + "…"
    # Mermaid mindmap が壊れる記号を全角/和記号へ退避
    trans = {'"': "'", "(": "（", ")": "）", "[": "［", "]": "］",
             "{": "｛", "}": "｝", "<": "「", ">": "」"}
    for k, v in trans.items():
        text = text.replace(k, v)
    return text


def build_markdown(session_id, recs, order):
    # 人間発言ノードを出現順に収集
    humans = [u for u in order if is_human(recs[u])]
    if not humans:
        return None

    # 畳み込みツリー: human -> 直近の human 親
    parent_of = {u: nearest_human_ancestor(u, recs) for u in humans}
    children = {}
    for u, p in parent_of.items():
        children.setdefault(p, []).append(u)

    # ノード採番(N1, N2, ...)
    nid = {u: f"N{i+1}" for i, u in enumerate(humans)}
    labels = {}
    for i, u in enumerate(humans):
        txt = extract_text(recs[u]["message"]["content"])
        labels[u] = f"{i+1}. {sanitize(txt)}"

    branch_points = {p for p, ch in children.items() if p and len(ch) > 1}

    # Mermaid mindmap 組み立て（インデント＝階層）
    roots = [u for u in humans if parent_of[u] is None]
    lines = ["```mermaid", "mindmap", f"  root(({session_id[:8]}))"]

    def walk(u, depth):
        label = labels[u]
        if u in branch_points:
            label = "🔀 " + label
        lines.append("  " * (depth + 1) + label)
        for c in children.get(u, []):
            walk(c, depth + 1)

    for r in roots:
        walk(r, 1)
    lines.append("```")
    mermaid = "\n".join(lines)

    # 発言一覧(全文・再開メモ付き)
    detail = []
    for i, u in enumerate(humans):
        txt = extract_text(recs[u]["message"]["content"]).strip()
        ts = recs[u].get("timestamp", "")
        flag = " 🔀分岐" if u in branch_points else ""
        detail.append(f"### {i+1}.{flag}\n\n"
                      f"- 時刻: `{ts}`\n"
                      f"- 再開: `claude --resume {session_id}` → 開いたら #{i+1} まで巻き戻す\n\n"
                      f"> {txt[:400]}")

    md = f"""---
sessionId: {session_id}
checkpoints: {len(humans)}
branches: {len(branch_points)}
tags: [chat-tree, claude-code]
---

# Chat Tree — `{session_id}`

再開方法: `claude --resume {session_id}` で開き、巻き戻しボタンで目的の番号まで戻る。
🔀 = 分岐点(同じ親から複数の枝)。

## ツリー

{mermaid}

## 発言一覧

{chr(10).join(detail)}
"""
    return md, len(humans), len(branch_points)


def resolve_path(arg):
    p = Path(arg)
    if p.exists():
        return p
    cand = PROJECT_DIR / f"{arg}.jsonl"
    if cand.exists():
        return cand
    return None


def hook_session_id():
    """Claude Code フックの stdin JSON から session_id を取り出す。"""
    try:
        data = json.load(sys.stdin)
        return data.get("session_id") or data.get("sessionId")
    except Exception:
        return None


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # フックモード: 終了したセッション1件だけ再生成
    if len(sys.argv) > 1 and sys.argv[1] == "--hook":
        sid = hook_session_id()
        if not sid:
            return
        path = resolve_path(sid)
        if not path:
            return
        recs, order = load_session(path)
        result = build_markdown(sid, recs, order)
        if result:
            md, n, b = result
            (OUT_DIR / f"{sid}.md").write_text(md, encoding="utf-8")
        return
    if len(sys.argv) > 1:
        path = resolve_path(sys.argv[1])
        if not path:
            print(f"見つかりません: {sys.argv[1]}")
            return
        files = [path]
    else:
        files = sorted(PROJECT_DIR.glob("*.jsonl"))

    index = ["# Chat Tree 一覧\n"]
    for f in files:
        sid = f.stem
        recs, order = load_session(f)
        result = build_markdown(sid, recs, order)
        if not result:
            continue
        md, n, b = result
        out = OUT_DIR / f"{sid}.md"
        out.write_text(md, encoding="utf-8")
        bp = f" / 分岐{b}" if b else ""
        index.append(f"- [[{sid}]] — 発言{n}件{bp}")
        print(f"出力: {out.name}  (発言{n}件, 分岐{b})")

    (OUT_DIR / "_index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"\n完了 → {OUT_DIR}")


if __name__ == "__main__":
    main()
