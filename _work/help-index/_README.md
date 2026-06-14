# _work/help-index/ — Help Center 記事 → P-スロット地図

**プランルール早見表（DBP_02 / P01-P19）の供給元を「Help Center の個別記事」単位で地図化する。**

## なぜ必要か（観測で確定した事実・2026-06-14）

- プランのルール（P01-P19）は **約99% が各ファームの Help Center / Q&A**、残りが**利用規約**から埋まる（マスター証言＋fundingpips実データで確認）。
- Help Center は「コレクション（ルールグループ）→ 個別ルール記事（例『ストップロスは必須ですか？』）」の階層構造。
- `firm-slot-urls.json` の粗い `Help Center → FAQ,F10-13` では P-スロットを測れない。**記事レベルの粒度**が要る。
- 旧 firm-tour/比較表/プラン個別ページは P-スロットの供給元として不適（観測で棄却済み）。

## スキーマ `{slug}.json`

```json
{
  "firm": "fundingpips",
  "help_base_url": "https://help.fundingpips.com/",
  "platform": "intercom",          // intercom / zendesk / helpscout / wordpress_faq / notion_public / inline_accordion / unknown / none / blocked
  "fetched_at": "2026-06-14",
  "fetch_status": "pending",        // pending / ok / partial / blocked / not_found
  "collections": [
    {
      "title": "Trading Rules",
      "url": "https://help.fundingpips.com/.../collections/xxx",
      "articles": [
        { "title": "Is a stop loss mandatory?", "url": "https://help.../articles/yyy", "slots": "P16" },
        { "title": "News trading policy",        "url": "https://help.../articles/zzz", "slots": "P10" }
      ]
    }
  ],
  "terms_sources": [                // 利用規約など Help Center 外の補助ソース（残り1%）
    { "title": "Terms and Conditions", "url": "https://.../terms", "slots": "P17,P19" }
  ]
}
```

- 各 `article.slots` = その記事が埋める P-スロット（カンマ区切り。`P01`〜`P20`）。1記事が複数Pを埋めることも、複数記事が1Pを埋めることもある。
- **網羅率（収集パネル Plan側）** = 全 `articles[].slots` ∪ `terms_sources[].slots` を集計し、P01-P20 のうち何項目に供給記事があるかで算出。

## P-スロット宇宙（早見表項目・MASTER_DEFS DBP_02 が正本）

| key | 項目 | key | 項目 |
|---|---|---|---|
| P20 | Steps | P10 | ニュース取引制限 |
| P01 | 利益目標 | P11 | 週末トレード制限 |
| P02 | 最低取引日数 | P12 | オーバーナイト制限 |
| P02b | 最低取引日数（出金） | P13 | EA制限 |
| P03 | 日次損失 | P14 | コピートレード制限 |
| P04 | 日次損失タイプ | P15 | スキャルピング制約 |
| P05 | 最大損失 | P16 | ストップロス制約 |
| P06 | 最大損失タイプ | P17 | リスクルール |
| P07 | 一貫性ルール | P18 | 最大ポジション制約 |
| P08 | 利益上限 | P19 | 禁止行為 |
| P09 | 時間制限 | | |

## 収集フロー（実記事の取得）

プラットフォーム別に最短ルートが違う：

### Zendesk（`/hc/...` 構造。例: fundingpips）★最も確実
全記事をAPIで一括取得でき、本文も同梱されるのでブラウズ不要：
```
curl -s "https://help.{firm}.com/api/v2/help_center/en-us/articles.json?per_page=100"
  → articles[].{id, title, html_url, body(HTML)}
```
1. APIで全記事リスト＋本文を取得
2. 本文をプレーン化し、P-スロット別キーワードで検索（例 P13="expert advisor", P18="lot size", P10="news"）→ どの記事が何を埋めるか**観測で確定**（推測しない）
3. `collections[].articles[].slots` に付与 → `coverage_observed` 算出

### Intercom / その他 / WAFブロック社
APIが無い/閉じている場合は Playwright MCP で `browser_navigate`+`browser_snapshot`、または NotebookLM/Web2MD補完。

### 共通
- モデル記事（各プランの説明）は P01-P09,P18,P20 をまとめて埋める（早見表本体）
- 横断ルール記事（News/Conduct/Responsible 等）が P10-P17,P19 を埋める
- 値が「なし」のスロット（例 P08利益上限）は、出典記事の**不記載**が根拠。`fetch_note` に明記
- 完了社は Firm Database 収集パネルの Plan網羅率（FD-16）に自動反映

## 履歴

- 2026-06-14: セッション18cで「READMEのみ・頓挫」として一度削除 → 同日復活。P-スロット供給元の地図として用途を明確化（記事→Pスロット対応・slots付与）。
