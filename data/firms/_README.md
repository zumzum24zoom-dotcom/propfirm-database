# data/firms/

**Firmマスターデータ。1ファーム = 1 JSON（`{slug}.json`）。**

- 正本: Page Maker (`01_tools/core/page-maker-v12.html`) の `MASTER_DEFS.dbp01`（22スロット）
- 出力: Page Maker の「Hugoエクスポート」ボタンで自動生成
- **手で編集しない**（次回エクスポートで上書きされる）

## スロット構成（DBP_01・22項目）

| カテゴリ | キー |
|---------|------|
| 基本 | firmName, country, established, officialUrl, firmCategory, japanChat |
| 特色 | firmPitch, rewardProgram, scaleUp |
| 取引 | broker, platform, serverTime, ddReset, leverage, commission |
| 入出金 | paymentMethods, payoutMethods, payoutPolicy, profitSplit, profitSplitNote |
| プラン | planComparison, planList |

詳細キー定義は `02_docs/page-maker-v11-analysis.md`、表記ルールは `data/glossary.json`。

## 新規ファーム追加手順

1. Page Maker で MASTER_DEFS を更新 → エクスポート
2. `content/firms/{slug}/index.md` を作成（frontmatter のみで可）
3. プランがあれば `data/plans/{slug}--{plan}.json` も同時生成

## 参照される場所

- `themes/pfd/layouts/firms/list.html` — 一覧
- `themes/pfd/layouts/_default/single.html` — 詳細
- `themes/pfd/layouts/api/list.json` — `/api/index.json` 出力
