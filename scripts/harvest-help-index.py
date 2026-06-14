#!/usr/bin/env python
"""harvest-help-index.py — Help Center を sitemap から収集し help-index を生成（FD-16の供給元）。

Intercom系（/articles/ をsitemapに列挙・記事ページがサーバー描画）を主対象に、
記事スラッグ/タイトルを P-スロット辞書で機械タグ付けする第一次パス。
出力 fetch_status="auto"（機械タグ＝要レビュー）。Zendesk は別途 API 経路（fundingpips参照）。

使い方:
  python scripts/harvest-help-index.py <slug>                # firm-slot-urls.json から help host 自動検出
  python scripts/harvest-help-index.py <slug> <sitemap_url>  # 明示
  python scripts/harvest-help-index.py --all-intercom        # 既知Intercom社を一括
"""
import json, re, sys, urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SLOT_URLS = ROOT / "_work" / "firm-slot-urls.json"
OUT_DIR = ROOT / "_work" / "help-index"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}

ALL_PLAN_SLOTS = ["P20","P01","P02","P02b","P03","P04","P05","P06","P07","P08","P09",
                  "P10","P11","P12","P13","P14","P15","P16","P17","P18","P19"]

# P-スロット → スラッグ/タイトル照合キーワード（正規表現・小文字）
KW = {
 "P01": [r"profit-target", r"profit-goal", r"what.*target"],
 "P02": [r"minimum-trading-days", r"trading-days", r"minimum-days", r"min-trading"],
 "P02b": [r"payout.*days", r"days.*payout", r"minimum.*(payout|withdraw)"],
 "P03": [r"daily-loss", r"daily-drawdown", r"daily-max", r"daily-limit"],
 "P04": [r"daily.*reset", r"reset-time", r"daily.*(calculated|based|type)"],
 "P05": [r"max-loss", r"maximum-loss", r"max-drawdown", r"overall-loss", r"maximum-drawdown", r"total-drawdown"],
 "P06": [r"trailing", r"static-drawdown", r"drawdown.*(calculated|type)", r"(balance|equity)-based"],
 "P07": [r"consistency"],
 "P08": [r"profit-cap", r"maximum-profit", r"capped"],
 "P09": [r"time-limit", r"how-long", r"expire", r"duration", r"inactivity", r"breach.*inactiv"],
 "P10": [r"news"],
 "P11": [r"weekend"],
 "P12": [r"overnight"],
 "P13": [r"expert-advisor", r"\beas?\b", r"-eas?-", r"automated", r"algorithmic", r"robots?"],
 "P14": [r"copy-trad", r"copier", r"copy.*allow"],
 "P15": [r"scalp"],
 "P16": [r"stop-loss", r"stop-out", r"without-stop"],
 "P17": [r"risk-per-trade", r"max-risk", r"risk-management", r"lot-limit", r"exposure"],
 "P18": [r"lot-size", r"maximum-lot", r"position-size", r"max-position", r"max-lot", r"lot-limit"],
 "P19": [r"prohibited", r"forbidden", r"not-allowed", r"violation", r"banned", r"hedging", r"martingale",
         r"arbitrage", r"grid", r"gambling", r"prohibited-strateg"],
 "P20": [r"steps?", r"phases?", r"one-step", r"two-step", r"three-step", r"\d-step", r"step-model"],
}

# 既知Intercom社（sitemap に /collections/ /articles/ が出た社）
INTERCOM = ["fundedelite","alpha-capital","aquafunded","atmos-funded","blueberry-funded",
            "e8-markets","finotive-funding","for-traders","top-one-trader","lark-funding",
            "brightfunded","fintokei"]


def fetch(url: str) -> str:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
        return r.read().decode("utf-8", "replace")


def help_host(slug: str) -> str | None:
    firms = json.loads(SLOT_URLS.read_text(encoding="utf-8"))["firms"]
    v = firms.get(slug) or {}
    for e in (v.get("slot_urls") or []):
        h = urlparse(e.get("url","")).netloc.lower()
        if h.split(".")[0] in ("help","support","faq","helpdesk","helpcenter"):
            return h
    return None


def _crawl_intercom(host: str) -> list[str]:
    """sitemap が無い Intercom Help Center 用: /en/ ＋ 各 /collections/ から /articles/ を集約。"""
    base = f"https://{host}"
    arts: set[str] = set()
    try:
        home = fetch(base + "/en/")
    except Exception:
        return []
    arts.update(re.findall(r"/(?:en/)?articles/[0-9][^\"#\s]*", home))
    cols = sorted(set(re.findall(r"/[a-z\-]*/?collections/[0-9][^\"#\s]*", home)))
    for c in cols[:40]:
        try:
            arts.update(re.findall(r"/(?:en/)?articles/[0-9][^\"#\s]*", fetch(base + c)))
        except Exception:
            pass
    return sorted(arts)


def slug_part(url: str) -> str:
    return url.rstrip("/").split("/")[-1].lower()


def titleize(s: str) -> str:
    parts = s.split("-")
    if parts and parts[0].isdigit():
        parts = parts[1:]
    return " ".join(parts)


def tag(text: str) -> list[str]:
    return [p for p, kws in KW.items() if any(re.search(k, text) for k in kws)]


def harvest(slug: str, sitemap: str | None = None) -> dict | None:
    host = urlparse(sitemap).netloc if sitemap else help_host(slug)
    if not host:
        print(f"  [skip] {slug}: help host 不明")
        return None
    sm = sitemap or f"https://{host}/sitemap.xml"
    arts = []
    try:
        locs = re.findall(r"<loc>([^<]+)</loc>", fetch(sm))
        arts = [u for u in locs if "/articles/" in u]
    except Exception:
        pass
    if not arts:
        # sitemap無し/記事無し → Intercom home(/en/)＋/collections/ を巡回して /articles/ を集約
        arts = _crawl_intercom(host)
    arts = [u if u.startswith("http") else f"https://{host}{u}" for u in arts]
    arts = [u.replace("http://", "https://") for u in arts]
    if not arts:
        print(f"  [skip] {slug}: /articles/ が見つからない（非Intercom?）")
        return None
    articles = []
    for u in sorted(set(arts)):
        sp = slug_part(u)
        articles.append({"title": titleize(sp), "url": u, "slots": ",".join(tag(sp))})
    cov = set(p for a in articles for p in a["slots"].split(",") if p)
    covered = [p for p in ALL_PLAN_SLOTS if p in cov]
    missing = [p for p in ALL_PLAN_SLOTS if p not in cov]
    return {
        "firm": slug,
        "help_base_url": f"https://{host}/",
        "platform": "intercom",
        "fetched_at": "2026-06-14",
        "fetch_status": "auto",
        "fetch_note": "sitemap→記事スラッグの機械タグ付け（第一次パス・要レビュー）。本文未取得。誤タグ/不足は手修正。",
        "collections": [{"title": "All articles（sitemap・自動タグ）", "articles": articles}],
        "terms_sources": [],
        "coverage_observed": {"covered": ",".join(covered), "missing": ",".join(missing),
                              "note": f"{len(covered)}/{len(ALL_PLAN_SLOTS)}（slug照合のみ）"},
    }


def write(hi: dict):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fp = OUT_DIR / f"{hi['firm']}.json"
    fp.write_text(json.dumps(hi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    c = hi["coverage_observed"]["covered"].split(",")
    print(f"  [ok] {hi['firm']:22} 記事{len(hi['collections'][0]['articles'])}  P網羅 {len(c)}/21 → {fp.relative_to(ROOT)}")


def main(argv):
    if not argv:
        print(__doc__); return
    if argv[0] == "--all-intercom":
        for s in INTERCOM:
            hi = harvest(s)
            if hi: write(hi)
        return
    slug = argv[0]
    sitemap = argv[1] if len(argv) > 1 else None
    hi = harvest(slug, sitemap)
    if hi: write(hi)


if __name__ == "__main__":
    main(sys.argv[1:])
