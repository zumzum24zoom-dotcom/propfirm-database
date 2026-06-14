#!/usr/bin/env python
"""refine-help-index.py — auto タグの help-index を記事本文で補強する第二次パス。

slug/質問文だけの機械タグ（fetch_status:"auto"）に対し、各記事の本文を実際に取得して
具体フレーズで照合し、取りこぼした P-スロット（P04/P06/P08等）を回収する。
- 過剰タグ回避のため、ゆるい単語ではなく具体フレーズで照合。
- 記事URLが個別（Intercom/custom_faq/wordpress_kb）の社のみ対象。
  inline_accordion（url=FAQページ共通）と fetch_status:"ok"（確定済み）はスキップ。
- 社ごとに取得上限（既定50）。超過分はルール関連タイトル優先＋ログ明示（無音切り捨てしない）。

使い方:
  python scripts/refine-help-index.py            # 対象社すべて
  python scripts/refine-help-index.py <slug> ... # 指定社のみ
  環境変数 CAP=80 で上限変更
"""
import json, os, re, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HI_DIR = ROOT / "_work" / "help-index"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}
CAP = int(os.environ.get("CAP", "50"))

ALL_PLAN_SLOTS = ["P20","P01","P02","P02b","P03","P04","P05","P06","P07","P08","P09",
                  "P10","P11","P12","P13","P14","P15","P16","P17","P18","P19"]

# 本文照合: 過剰タグ回避のため具体フレーズ（小文字・正規表現）
BODY_KW = {
 "P01": [r"profit target", r"profit goal", r"target of \d", r"reach .{0,10}% profit"],
 "P02": [r"minimum (of )?\d+ trading days", r"minimum trading days", r"minimum number of trading days", r"\d+ (active )?trading days"],
 "P02b": [r"before (requesting|your first) (a )?(payout|withdraw)", r"minimum .{0,20}(payout|withdrawal)", r"first payout after \d"],
 "P03": [r"daily (loss|drawdown) (limit)?", r"maximum daily loss", r"max daily loss", r"daily limit of"],
 "P04": [r"balance or equity", r"equity[- ]based", r"based on .{0,12}balance", r"higher of .{0,20}(balance|equity)",
         r"end[- ]of[- ]day balance", r"starting balance of (the|each) day", r"calculated .{0,15}balance"],
 "P05": [r"maximum (overall |total )?(loss|drawdown)", r"max (overall |total )?(loss|drawdown)", r"overall loss limit"],
 "P06": [r"trailing drawdown", r"static drawdown", r"trailing .{0,10}(loss|drawdown)", r"drawdown .{0,12}(trailing|static)",
         r"locks (in|at)", r"end[- ]of[- ]day drawdown", r"relative drawdown", r"absolute drawdown"],
 "P07": [r"consistency (rule|score|requirement)"],
 "P08": [r"profit cap", r"maximum profit", r"no (profit )?cap", r"profit is capped", r"cap on .{0,8}profit"],
 "P09": [r"time limit", r"no time limit", r"unlimited time", r"\d+ calendar days", r"days to (complete|pass)",
         r"inactivity", r"account .{0,10}expire"],
 "P10": [r"news (trading|events)", r"red folder", r"high[- ]impact news", r"during .{0,10}news"],
 "P11": [r"over the weekend", r"weekend holding", r"hold .{0,15}weekend", r"weekend (trading|positions)"],
 "P12": [r"overnight (position|trading|hold)", r"hold .{0,10}overnight"],
 "P13": [r"expert advisor", r"\beas?\b", r"automated (trading|strateg)", r"algorithmic", r"trading bots?"],
 "P14": [r"copy trad", r"copier", r"copy .{0,8}(account|signal)"],
 "P15": [r"scalp"],
 "P16": [r"stop[- ]loss", r"stop loss"],
 "P17": [r"risk per trade", r"maximum risk", r"risk management rule", r"max(imum)? exposure", r"risk per position"],
 "P18": [r"(maximum|max) lot", r"lot size limit", r"position size limit", r"maximum .{0,8}position", r"max(imum)? lots?"],
 "P19": [r"prohibited", r"forbidden", r"not allowed", r"hedging", r"martingale", r"arbitrage", r"gambling",
         r"grid trading", r"banned", r"prohibited trading"],
 "P20": [r"\b(one|two|three|1|2|3)[- ]step", r"\d+ phase", r"evaluation phase", r"phase \d", r"number of (steps|phases)"],
}
RULE_TITLE = re.compile(r"loss|drawdown|rule|news|weekend|overnight|stop|lot|position|consistency|scalp|"
                        r"expert|copy|daily|target|days|time|breach|prohibit|hedg|martingale|step|phase|"
                        r"objective|model|evaluation|risk|leverage", re.I)


def fetch_text(url: str) -> str | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=12) as r:
            raw = r.read(400000).decode("utf-8", "replace")
    except Exception:
        return None
    t = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).lower()


def tag_body(text: str) -> set:
    return {p for p, kws in BODY_KW.items() if any(re.search(k, text) for k in kws)}


def slots_set(a):
    return set(s for s in (a.get("slots") or "").split(",") if s)


def cov_count(hi):
    cov = set()
    for c in hi.get("collections", []):
        for a in c.get("articles", []):
            cov |= slots_set(a)
    for t in hi.get("terms_sources", []):
        cov |= slots_set(t)
    return [p for p in ALL_PLAN_SLOTS if p in cov]


def refine(fp: Path) -> bool:
    hi = json.loads(fp.read_text(encoding="utf-8"))
    if hi.get("platform") == "inline_accordion" or hi.get("fetch_status") == "ok":
        print(f"  [skip] {hi['firm']}: {hi.get('platform')}/{hi.get('fetch_status')}")
        return False
    arts = [a for c in hi.get("collections", []) for a in c.get("articles", []) if a.get("url")]
    # 同一URL重複は1回だけ取得
    uniq = {}
    for a in arts:
        uniq.setdefault(a["url"], []).append(a)
    urls = list(uniq.keys())
    if len(urls) > CAP:
        urls.sort(key=lambda u: 0 if RULE_TITLE.search(u) else 1)  # ルール系URL優先
        dropped = len(urls) - CAP
        urls = urls[:CAP]
    else:
        dropped = 0
    before = cov_count(hi)
    fetched = 0
    for u in urls:
        txt = fetch_text(u)
        if not txt:
            continue
        fetched += 1
        found = tag_body(txt)
        for a in uniq[u]:
            merged = sorted(slots_set(a) | found, key=lambda s: ALL_PLAN_SLOTS.index(s) if s in ALL_PLAN_SLOTS else 99)
            a["slots"] = ",".join(merged)
    after = cov_count(hi)
    hi["fetch_status"] = "auto+body"
    note = hi.get("fetch_note", "")
    hi["fetch_note"] = note + f" / 本文補強: {fetched}記事取得・本文具体フレーズ照合でslot追加" + (f"（上限{CAP}超で{dropped}記事は未取得＝ルール系優先）" if dropped else "")
    hi["coverage_observed"]["covered"] = ",".join(after)
    hi["coverage_observed"]["missing"] = ",".join(p for p in ALL_PLAN_SLOTS if p not in after)
    hi["coverage_observed"]["note"] = f"{len(after)}/{len(ALL_PLAN_SLOTS)}（本文補強後）"
    fp.write_text(json.dumps(hi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cap_msg = f" [上限超{dropped}未取得]" if dropped else ""
    print(f"  [ok] {hi['firm']:22} 取得{fetched:3} 網羅 {len(before)}→{len(after)}/21{cap_msg}")
    return True


def main(argv):
    targets = ([HI_DIR / f"{s}.json" for s in argv] if argv
               else sorted(p for p in HI_DIR.glob("*.json") if not p.stem.startswith("_")))
    for fp in targets:
        if fp.exists():
            try:
                refine(fp)
            except Exception as e:
                print(f"  [err] {fp.stem}: {e}")


if __name__ == "__main__":
    main(sys.argv[1:])
