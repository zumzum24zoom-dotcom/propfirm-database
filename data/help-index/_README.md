# data/help-index/

**全ファームのHelp Center / FAQ構造インデックス。**

スロット項目抽出（DBP_02埋め）の前段。「どの記事に何が書いてあるか」の地図を一度きり全社分作成し、その後の正規化はインデックス参照で効率化する。

## 構成

| ファイル | 内容 |
|---------|------|
| `_README.md` | 本ファイル |
| `_classification.json` | 全社のHelp Centerプラットフォーム分類 |
| `{firmSlug}.json` | 1ファームあたり1ファイル |

## `{firmSlug}.json` スキーマ

```json
{
  "firm": "city-traders-imperium",
  "official_url": "https://citytradersimperium.com/",
  "help_base_url": "https://helpcenter.citytradersimperium.com/en",
  "platform": "intercom",
  "fetch_status": "ok",
  "fetched_at": "2026-06-10",
  "collections": [
    {
      "title": "Essential Rules & Guidelines",
      "url": "https://helpcenter.citytradersimperium.com/en/collections/16756321-...",
      "article_count": 12,
      "articles": [
        {
          "title": "Stop Loss Rule",
          "url": "https://helpcenter.citytradersimperium.com/en/articles/12879278-...",
          "preview": "Our data shows that traders who trade without a stop-loss usually don't last long..."
        }
      ]
    }
  ],
  "notes": "Intercom-based help center. Same-origin fetch works in browser context."
}
```

## platform 分類

| platform | 特徴 | 取得方法 |
|----------|------|---------|
| `intercom` | `helpcenter.*.com` / `help.*.com` (Intercom hosted) | browser_evaluate同一オリジンfetch |
| `zendesk` | `*.zendesk.com` または `support.*.com` | 同上 |
| `helpscout` | `*.helpscout.net` | 同上 |
| `wordpress_faq` | 公式サイト内のFAQページ（プラグイン） | WebFetch |
| `notion_public` | Notion公開ページ | WebFetch |
| `inline_accordion` | 公式トップ内のアコーディオンFAQ | scanのpageTextで代用可 |
| `unknown` | 構造不明・要個別調査 | 手動 |
| `none` | Help Center自体が存在しない | — |
| `blocked` | 取得失敗（403/CAPTCHA等） | 別経路検討 |

## fetch_status

- `ok` — 全Collection + 全Articleタイトル取得済
- `partial` — Collectionは取れたが一部Articleが取れない
- `blocked` — 認証/403/CAPTCHAで取得不可
- `not_found` — Help Center URL自体が見つからない

## 更新フロー

1. `scripts/build-help-index.py` … 本来は単体スクリプト化したいが、現状はClaudeがPlaywright MCPで直接実行
2. 各ファームごとに `{slug}.json` を書き出し
3. 完了後 `_classification.json` を再生成
4. 失敗ファームは `_classification.json` の `blocked` または `unknown` に分類

## 利用方法（後段スキル）

`/normalize-firm <slug>` スキルが本インデックスを参照：
1. `data/help-index/{slug}.json` を読む
2. 22スロットの各項目に対し「どの記事を読むべきか」をLLMで選定
3. 該当記事のみfetch → 正規化 → `data/plans/{slug}--{plan}.json.draft` 出力

## 注意

- Help Centerは更新される。インデックスは陳腐化する前提（3〜6か月ごと再生成推奨）
- `_classification.json` は手で書かない。本ファイル群を集計して自動生成
