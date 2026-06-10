# Claude チャット用コンテキスト — Prop Firm Challengers

> **用途**: Claude.ai（Web UI）のプロジェクト知識ファイルとしてアップロードするための圧縮コンテキスト。
> Claude Code ローカル環境とWeb UI の両方で同じ前提に立たせるための共有資料。
> **最終更新**: 2026-06-08

---

## 1. プロジェクト基本情報

- **名称**: Prop Firm Database（略称: PFD）
- **目的**: 世界中のプロップトレーディングファームを比較・攻略する日本語情報サイト
- **技術スタック**: Hugo + Netlify + GitHub
- **作業ディレクトリ**: `D:\vs code\propfirm-database`
- **GitHub**: https://github.com/zumzum24zoom-dotcom/propfirm-database
- **ブランチ**: master

## 2. 役割分担（厳守）

- **マスター（ユーザー）**: 戦略立案者、情報設計判断、コンテンツ方針決定
- **ソートー（Claude）**: 技術補佐・Hugo実装・フロントエンド・選択肢提示

### ソートーの行動原則
- 戦略・マーケ提案・情報設計の方向性決定は**マスター領域**（越権禁止）
- 「○○を実現するには技術的に△△が必要」型の補佐に徹する
- 複雑タスク着手前: 「このタスクは複雑です。トークン消費を度外視して全力で取り組みますか？ (y/n)」確認
- マスター指示形式: a/b/c の選択肢提示。JSON フォーマット禁止
- マスターは短文単文字で返すことが多い → 簡潔・明確な応答

## 3. 用語

| 略号 | 意味 |
|---|---|
| DBP_01 | Firm（ファーム）テンプレート。22スロット |
| DBP_02 | Plan（プラン）テンプレート。22スロット |
| C / F | Challenge / Funded（評価フェーズ／資金提供後フェーズ）|
| 攻略3断面 | DD / 取引ルール / 出金 の3セクション攻略記事 |
| 攻略個社 | 1ファームに特化した攻略記事 |
| 攻略横断 | 複数ファーム比較の攻略記事 |
| ソートー | Claude（プロジェクト内呼称）|

## 4. システム構成（3層パイプライン）

```
NotebookLM（情報収集）  →  Page Maker（整形・スロット格納）  →  Hugo（公開）
                                       ↓
                                 pfdb.json（正本）
                                       ↓
                          data/firms/{slug}.json / data/plans/{slug}.json
                                       ↓
                          content/firms/{slug}/_index.md
```

### 各レイヤの責務

- **NotebookLM**: ファーム公式サイトを構造化データ＋攻略記事として出力
- **Page Maker**（`01_tools/core/page-maker-v12.html`）: 入力ツール。スロット格納・整形・Hugo出力
- **Hugo + Netlify**: 公開サイト

## 5. データモデルの正本

`MASTER_DEFS` = **唯一の正本**（page-maker-v12.html 内）

```
MASTER_DEFS
  ├ dbp01[22件]  Firmスロット定義
  ├ dbp02[22件]  Planスロット定義
  └ koryaku[3件] 攻略3断面（k_dd / k_rules / k_payout）
       ↓ 派生（自動生成）
  ├ SLOT_DEFS      ← Page Maker UI右ペイン
  ├ FIRM_KEY_MAP   ← Hugo出力時のスロットID↔日本語キー対応
  ├ PLAN_KEY_MAP   ← 同上（Plan用）
  ├ F_KEY_MAP      ← 表取込時のF01〜F22 → slot id
  └ GLOSSARY_SEED  ← 用語辞典の Firm項目 + Plan項目
                    + GLOSSARY_BASE（表記ルール・計算結果列名）
```

**MASTER_DEFSのみ編集する。** 派生定数は直接編集禁止。

## 6. 公開ページのURL構造（P012で確定）

| ページ | パス |
|---|---|
| ホーム | `/` |
| Firm一覧 | `/firms/` |
| Firm個社ページ | `/firms/{slug}/` |
| プラン詳細 | `/firms/{firmSlug}/{planSlug}/` |
| 攻略記事 | `/articles/{slug}/` |

- 言語: 英語スラッグ統一
- **絶対原則**: 公開ページのURL削除禁止（404→SEO損失）

## 7. 主要ツール（01_tools/）

01_toolsは用途別フォルダで整理:
- `core/` — 本体ツール（page-maker-v12, sitemap-designer, widget-maker, firm-tour）
- `coupon/` — クーポン関連（Coupon Sidebar, coupon-fetcher, Dom scanner BMT）
- `analysis/` — トレード分析・計算ツール（Consistency Planner等）
- `chat/` — テキスト・LLM補助（chat-tree, text-structurer）
- `utils/` — 開発ユーティリティ（BLT＝ブックマークレット集、html文章掃除、draft-viewer等）
- `_archive/` — propfirm-database非関連のアーカイブ

| ファイル | 用途 |
|---|---|
| `core/page-maker-v12.html` | データ入力・整形・Hugo出力エンジン |
| `core/sitemap-designer.html` | サイト構造（ナビゲーション）設計ツール |
| `core/widget-maker.html` | ウィジェット生成（試作） |

### Page Maker v12 の主要機能

- 23ファーム × 全プランデータの正本管理（pfdb.json）
- スロット入力UI（左ペイン）
- 用語辞典管理（右ペイン切替）
- 価格マトリクスエディタ
- ルールテーブルエディタ（rd_*）
- 自動振り分け（Sonnet AI）
- 攻略3断面生成（Sonnet AI、ただし NotebookLM 直接取込推奨）
- **NotebookLM出力の自動分割取込**（決定的パーサ）
- **プロンプト管理ページ**（9プロンプトの中央化・A/B比較・自己リント・相談用コピー）
- Hugo出力（exportHugo: data/firms, data/plans, content/firms, content/plans）
- 自動保存（localStorage）+ JSON保存/読込
- マージ機能（複数マシン作業の統合）

### Sitemap Designer

- ページ構造（カード階層）をDnDで編集
- 分身ノード（多重所属表現）+ SVG点線接続
- 2タブ式: ページ構造 / ページ内容（ブロック編成）
- P026書出（公開ページ構造の正本Markdown生成）

## 8. Sonnet が担う処理（Page Maker内）

NotebookLMが収集した情報をPage Maker内で**Sonnet APIが再処理**する処理:

| 機能 | 用途 |
|---|---|
| OCR（画像→テキスト）| 画像Drop時の抽出 |
| 翻訳 EN→JP | 貼付テキストの翻訳 |
| 断片統合 | 同一スロット内の複数断片を1つに整形 |
| 単スロット整形 | 対象スロットへの抽出整形 |
| 自動振り分け | テキスト→複数スロットJSON振り分け |
| 攻略3断面生成 | Firm+Planデータから3断面HTML生成（※NotebookLM直接取込推奨） |
| プラン比較テーブル生成 | DBP_01用 |
| 用語登録 | 用語辞典エントリ抽出 |

全プロンプトは `PROMPTS_REGISTRY` で中央管理（page-maker-v12.html L3110付近）。

## 9. 用語辞典の役割

- 表記ルールの正本（Challenge/Funded統一、DD計算基準6分類、不在表記「ー / なし / 記載なし」の区別）
- 全Sonnetプロンプトに動的注入される
- スロット定義との違い: スロット定義=「どこに入れるか」、用語辞典=「どう表記するか」
- 右ペインで編集可能、pfdb.json に保存

## 10. 攻略記事の方針（P005/P006/P022）

### 2層構造（正本層 / 独自分析層）

- **正本層** = Firm/Planページ（事実の羅列、PFC主観なし）
- **独自分析層** = 攻略記事（PFCフィルターを通した評価・分析）

### 攻略記事の2種類

| 種類 | 内容 | URL |
|---|---|---|
| 横断比較攻略 | 複数Firmを軸で比較 | `/articles/{theme}/` |
| 個社攻略 | 1社特化の深掘り | `/articles/{slug}/` |

### 攻略3断面（NotebookLM生成）

```
## 断面① Drawdown          → k_dd
## 断面② 取引ルール         → k_rules
## 断面③ 出金までの流れ      → k_payout
```

**運用フロー（最短）**:
1. NotebookLM で攻略3断面生成（Markdownテーブル形式）
2. 全文クリップボードコピー
3. Page Maker 攻略タブの **「📋 NotebookLM取込」** ボタン
4. → k_dd / k_rules / k_payout に自動分割格納
5. 🚀 Hugo ボタン → 公開

## 11. 現状の進捗（2026-06-08時点）

### ✅ 完了

- Page Maker v12 稼働中（33ファーム充填）
- 全33ファームの `_index.md` 作成済み
- `data/firms/*.json` 33件　中身なし30件　3件有
- `data/plans/*.json` 中身なし
- Hugo個社ページ表示確認
- プロンプト管理ページ実装
- NotebookLM分割取込実装
- Sitemap Designer v1実装
- 全ファイル GitHub push 済み

### 🟡 進行中・未完

- 攻略3断面の見た目調整（Markdownテーブル → rule-table 統一）
- プランページのFirm個社ページ統合検討
- 攻略専用ページ `/articles/` の本格実装
- トップページ統計カウントの実装
- Sitemap Designer でマスター構想を確定 → P026書出

### ❌ 未着手

- Netlify本番デプロイ
- ドメイン接続
- アフィリエイト/クーポン全ファーム整備
- プラン横断比較ページ
- 検索・絞り込み機能
- GA4 アクセス解析

## 12. ロードマップ概要

```
Phase 1: 公開最小構成（表示の整合・トップ統計・攻略レンダラ）
Phase 2: コンテンツ充実（全ファーム攻略生成・価格補完・SEO）
Phase 3: 検索・絞り込み（フィルターUI・全文検索）
Phase 4: 収益化導線（クーポン本番化・アフィリエイト全件）
Phase 5: 本番デプロイ（Netlify・ドメイン）
Phase 6: 運用基盤（自動デプロイ・月次更新フロー）
Phase 7（オプション）: 拡張機能（比較表・レビュー・多言語）
```

## 13. 重要ポリシー（zz_notes/policy/）

| ID | 内容 |
|---|---|
| P001 | 掲載ポリシー（情報ソース方針） |
| P002 | 公開サイトに根拠URL記載しない方針 |
| P003 | 掲載ポリシー（記載なし と なし の区別） |
| P005 | サイト構築方針2層構造（正本/攻略） |
| P006 | 攻略記事の個社ページ構成方針 |
| P012 | パーマリンク設定仕様 |
| P020 | 用語統一（DB02 11項目） |
| P022 | 攻略コンテンツ2層構造方針 |

## 14. 既知の制約・注意事項

- Page Maker の `exportHugo` は **File System Access API 依存**（Chromium系ブラウザのみ）
- LLM 呼出は Cloudflare Worker プロキシ `/api/llm` 経由（`claude-sonnet-4-20250514`）
- Hugo は `data/firms` `data/plans` が空だと build エラー → nil-safe にテンプレ修正済み
- `_index.md` が無いと Firm個社ページが renderされない（type: firm 必須）

## 15. セッション継承

- **Claude Code側**: `02_docs/HANDOFF.md` を起動時に必ず読む
- **Claude.ai側（このファイル）**: プロジェクト知識にアップロードして共有
- **両者の整合**: 大方針はこのファイルに集約、詳細はHANDOFF.mdが正本

---

## Appendix A: ディレクトリ構成

```
propfirm-database/
├── 01_tools/          ← 開発ツール群（用途別フォルダ整理済み）
│   ├── core/         ← 本体パイプライン
│   ├── coupon/       ← クーポン
│   ├── analysis/     ← トレード分析
│   ├── chat/         ← テキスト補助
│   ├── utils/        ← 開発補助
│   └── _archive/     ← 非関連アーカイブ
├── 02_docs/           ← ドキュメント
│   ├── HANDOFF.md     ← Claude Code用引継ぎ
│   └── CLAUDE_CONTEXT.md ← Claude.ai用（このファイル）
├── archetypes/
├── content/
│   └── firms/         ← 各Firmの _index.md と配下プラン
├── data/
│   ├── firms/         ← Firmデータ正本JSON
│   ├── plans/         ← Planデータ正本JSON
│   └── glossary.json  ← 用語辞典
├── themes/
│   └── pfd/
│       ├── layouts/
│       │   ├── _default/
│       │   ├── firm/list.html     ← Firm個社ページ
│       │   ├── firms/list.html    ← Firm一覧
│       │   ├── plans/single.html  ← Plan詳細
│       │   └── plans/list.html    ← Plan一覧
│       └── static/css/style.css
├── zz_notes/
│   ├── policy/        ← 設計方針正本
│   └── impl/          ← 実装メモ
├── CLAUDE.md          ← Claude Code起動時必読
├── hugo.yaml
└── netlify.toml
```

## Appendix B: マスター情報

- 私用Notion: DB_000_Policy / DB_100_Impl
- 主要ファーム取り扱い: FTMO / The5ers / FundedNext / FundingPips / FundedElite / TopOneTrader 他27社
- 日本人ターゲット（日本語サイト構築）
