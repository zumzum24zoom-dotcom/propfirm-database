# data/plans/

**Planマスターデータ。1プラン = 1 JSON（`{firmSlug}--{planSlug}.json`）。**

- 正本: Page Maker `MASTER_DEFS.dbp02`（22スロット + P02b extra）
- 出力: Page Makerエクスポートで自動生成
- **手で編集しない**

## ファイル名規則

`{firmSlug}--{planSlug}.json`
例: `ftmo--challenge-10k.json`, `fundednext--stellar-2-step.json`

ダブルハイフン `--` が firm/plan の区切り。

## スロット構成（DBP_02・22項目）

| カテゴリ | キー |
|---------|------|
| 基本 | challengeName, priceTable, ruleQuickRef |
| ルール詳細 | rd_target, rd_minDays, rd_dailyLoss(+Type), rd_maxLoss(+Type), rd_consistency, rd_profitCap, rd_timeLimit, rd_news, rd_weekend, rd_overnight, rd_ea, rd_copyTrade, rd_scalping, rd_stopLoss, rd_risk, rd_maxPosition, rd_prohibited |
| その他 | steps（P20）, extra（P02b） |

## 参照される場所

- `themes/pfd/layouts/plans/single.html` — 詳細
- `themes/pfd/layouts/plans/list.html` — 一覧

`content/plans/{slug}.md` の frontmatter `params.dataKey` で対応JSONを指定する設計（要確認）。
