# _work/ — 作業層（Hugo対象外）

> **このフォルダは公開サイトに出ない作業中間物の置き場。** Hugoは `data/` 配下しか描画に使わない（`Data.firms` / `Data.plans`）。ドラフト・収集生データ・統合DB・状態ファイルを `data/` から分離し、公開層を汚さないために設けた（2026-06-14・設計判断#12）。

## 中身

| パス | 役割 | 触るもの |
|------|------|---------|
| `firms-edit/{slug}.json` | page-maker改「1社モード」の編集ドラフト | agent.py `/api/firm-edit` |
| `firms-v2/{slug}.md` | v2正規化ソース（1社1file・全プラン内包） | `/normalize-firm-v2` スキル → Page Maker取込 |
| `scans/` | Web2MD生ダンプ（記事単位）。**gitignore対象**（再取得可） | Web2MD拡張Download → `split-web2md-dump.mjs` |
| `price-collect/` | 価格収集生データ＋`wide/`（横持ち変換結果） | `convert-price-tables.mjs` / `verify-price-tables.mjs` |
| `progress.json` | Firm Database の制作ステータス | agent.py `/api/progress` |
| `firm-slot-urls.json` | URLレジストリ（32社・URL↔スロット対応マップ） | Firm Database 収集コックピット（FD-11〜15）が読む |
| `url-health.json` | URL生死チェックのキャッシュ（FD-12が生成・更新） | agent.py `/api/url-health` |

## ルール

- **公開データ（`data/firms/` `data/plans/` `data/glossary.json` `data/coupon-config.json`）はここに置かない。** 逆も同様。
- `firms-edit` → 公開 `data/firms/` への昇格は Page Maker「Hugoエクスポート」が担う。
- 構造の正本は `PROJECT_MAP.md`、進捗は `02_docs/HANDOFF.md`。

## 廃棄済み（2026-06-14・v1ゴミ一掃）

- `pfdb.json`（v1統合DB）/ `firms-edit/*.json`(33・v1ドラフト) / `help-index/`（READMEのみ・頓挫）/ `_legacy/firm-urls.json`（死蔵）/ `scripts/split-pfdb-to-edit.mjs`（pfdb→firms-edit生成・用済み）。すべて git 履歴に残存。glossaryは `data/glossary.json`(149) が上位集合のため損失なし。
