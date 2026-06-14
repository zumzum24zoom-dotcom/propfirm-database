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


def strip_injected(text):
    """ハーネスが注入する ide_opened_file / system-reminder ブロックを除去。"""
    text = re.sub(r"<ide_opened_file>.*?</ide_opened_file>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<system-reminder>.*?</system-reminder>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)  # 残りの簡易タグ
    return text


def topic_slug(text, limit=24):
    """発言テキストから Windows ファイル名に使える話題スラッグを作る。"""
    text = strip_injected(text)
    text = re.sub(r"\s+", " ", text).strip()
    # Windows 禁止文字 + パス区切りを除去/置換
    text = re.sub(r'[\\/:*?"<>|]', "", text)
    text = text.replace(" ", "_")
    text = text.strip("._")
    if not text:
        text = "無題"
    if len(text) > limit:
        text = text[:limit]
    return text


def touched_files(recs, order):
    """セッション内の Write/Edit/NotebookEdit が触ったファイルを
    VAULT_ROOT 相対パスの集合で返す（順序保持）。"""
    seen = []
    for u in order:
        m = recs[u].get("message", {})
        c = m.get("content")
        if not isinstance(c, list):
            continue
        for x in c:
            if isinstance(x, dict) and x.get("type") == "tool_use" \
                    and x.get("name") in ("Write", "Edit", "NotebookEdit"):
                fp = x.get("input", {}).get("file_path") or x.get("input", {}).get("notebook_path")
                if not fp:
                    continue
                p = fp.replace("\\", "/")
                root = str(VAULT_ROOT).replace("\\", "/")
                if p.lower().startswith(root.lower()):
                    p = p[len(root):].lstrip("/")
                if p not in seen:
                    seen.append(p)
    return seen


def human_fingerprint(recs, order):
    """セッションの人間発言テキスト列（正規化）を返す。fork判定の指紋。"""
    fp = []
    for u in order:
        if is_human(recs[u]):
            t = re.sub(r"\s+", " ", extract_text(recs[u]["message"]["content"])).strip()
            fp.append(t)
    return fp


def dedup_files(files):
    """resume で複製された fork セッションを畳み込む。
    発言列が完全一致 or 一方が他方の先頭一致(prefix)なら、発言数が多い方
    （= 最新の復元/継続版）だけ残す。残す jsonl パスのリストを返す。"""
    sessions = []
    for f in files:
        recs, order = load_session(f)
        fp = human_fingerprint(recs, order)
        if fp:
            sessions.append((f, fp))
    # 発言数が多い順 → 既存keeperと7割以上重なる短い枝(resume fork)は捨てる
    sessions.sort(key=lambda s: len(s[1]), reverse=True)
    kept = []
    for f, fp in sessions:
        superseded = False
        for _, kfp in kept:
            if len(fp) > len(kfp):
                continue
            # 共通先頭長を測る
            common = 0
            for x, y in zip(fp, kfp):
                if x == y:
                    common += 1
                else:
                    break
            # 完全な先頭一致、または短い側の7割以上が本線と一致 = 同一/fork
            if common == len(fp) or (common >= 2 and common >= 0.7 * len(fp)):
                superseded = True
                break
        if not superseded:
            kept.append((f, fp))
    return [f for f, _ in kept]


def out_filename(session_id, recs, order):
    """日付__話題__短縮UUID.md のファイル名を生成。"""
    humans = [u for u in order if is_human(recs[u])]
    first = humans[0] if humans else None
    date = ""
    topic = "無題"
    if first:
        ts = recs[first].get("timestamp", "")
        date = ts[:10] if len(ts) >= 10 else ""
        topic = topic_slug(extract_text(recs[first]["message"]["content"]))
    short = session_id[:8]
    prefix = f"{date}__" if date else ""
    return f"{prefix}{topic}__{short}.md"


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

    # 発言一覧(見出しに発言冒頭・本文に全文)
    detail = []
    for i, u in enumerate(humans):
        raw = strip_injected(extract_text(recs[u]["message"]["content"])).strip()
        head = sanitize(raw, 60) or "（空）"
        ts = recs[u].get("timestamp", "")[:19].replace("T", " ")
        flag = " 🔀" if u in branch_points else ""
        body = "\n".join("> " + ln for ln in raw[:600].splitlines()) or "> （本文なし）"
        detail.append(f"### {i+1}. {head}{flag}\n\n"
                      f"`{ts}`\n\n"
                      f"{body}")

    files = touched_files(recs, order)
    if files:
        files_section = "\n".join(f"- [{p}]({p})" for p in files)
    else:
        files_section = "_（Write/Edit による変更なし）_"

    md = f"""---
sessionId: {session_id}
checkpoints: {len(humans)}
branches: {len(branch_points)}
files: {len(files)}
tags: [chat-tree, claude-code]
---

# Chat Tree — `{session_id}`

再開方法: `claude --resume {session_id}` で開き、巻き戻しボタンで目的の番号まで戻る。
🔀 = 分岐点(同じ親から複数の枝)。

## 変更ファイル

{files_section}

## ツリー

{mermaid}

## 発言一覧

{(chr(10)+chr(10)).join(detail)}
"""
    return md, len(humans), len(branch_points), files


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
            md, n, b, _files = result
            # 旧名（{uuid}.md や別話題の同セッション）を掃除してから書く
            for old in OUT_DIR.glob(f"*{sid[:8]}*.md"):
                old.unlink()
            stale = OUT_DIR / f"{sid}.md"
            if stale.exists():
                stale.unlink()
            # resume 元（このセッションの発言列の先頭一致になる旧 fork）の生成物を除去
            cur_fp = human_fingerprint(recs, order)
            for other in PROJECT_DIR.glob("*.jsonl"):
                osid = other.stem
                if osid[:8] == sid[:8]:
                    continue
                ofp = human_fingerprint(*load_session(other))
                if ofp and len(ofp) <= len(cur_fp) and cur_fp[:len(ofp)] == ofp:
                    for dup in OUT_DIR.glob(f"*{osid[:8]}*.md"):
                        dup.unlink()
            (OUT_DIR / out_filename(sid, recs, order)).write_text(md, encoding="utf-8")
        return
    if len(sys.argv) > 1:
        path = resolve_path(sys.argv[1])
        if not path:
            print(f"見つかりません: {sys.argv[1]}")
            return
        files = [path]
    else:
        files = sorted(PROJECT_DIR.glob("*.jsonl"))
        files = dedup_files(files)   # resume 複製を畳み込む

    # 全再生成時は既存の生成物を一掃（_index.md は残す）してから作り直す
    for old in OUT_DIR.glob("*.md"):
        if old.name != "_index.md":
            old.unlink()

    index = ["# Chat Tree 一覧\n"]
    file_map = {}   # ファイルパス -> [(セッション名, 発言数)]
    for f in files:
        sid = f.stem
        recs, order = load_session(f)
        result = build_markdown(sid, recs, order)
        if not result:
            continue
        md, n, b, touched = result
        out = OUT_DIR / out_filename(sid, recs, order)
        out.write_text(md, encoding="utf-8")
        bp = f" / 分岐{b}" if b else ""
        fc = f" / 📄{len(touched)}" if touched else ""
        index.append(f"- [[{out.stem}]] — 発言{n}件{bp}{fc}")
        print(f"出力: {out.name}  (発言{n}件, 分岐{b}, ファイル{len(touched)})")
        for p in touched:
            file_map.setdefault(p, []).append(out.stem)

    (OUT_DIR / "_index.md").write_text("\n".join(index) + "\n", encoding="utf-8")

    # 逆引き索引: ファイル → 触ったセッション
    rev = ["# ファイル → 編集したチャット（逆引き）\n",
           "各ファイルを Write/Edit したセッションの一覧。\n"]
    for p in sorted(file_map):
        rev.append(f"## [{p}]({p})")
        for stem in file_map[p]:
            rev.append(f"- [[{stem}]]")
        rev.append("")
    (OUT_DIR / "_files-index.md").write_text("\n".join(rev) + "\n", encoding="utf-8")
    print(f"\n完了 → {OUT_DIR}")


if __name__ == "__main__":
    main()
