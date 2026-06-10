# 引き継ぎ資料 — Prop Firm Challengers / propfirm-database

> **運用ルール**: このファイル1枚を上書き更新する。セッション開始時はまずこれを読む。
> **最終更新**: 2026-06-10（セッション11）

---

## 【セッション11・2026-06-10】normalize-firm --all 完了

### 作業内容

`normalize-firm --all` を実行。全30社（out_of_scope 1 + blocked 1 + own_site 1 除く）の `data/firms/{slug}.pipe.md` を生成。

| 状態 | 件数 |
|------|------|
| 新規生成 | 30社 |
| 既存（スキップ） | 1社（city-traders-imperium） |
| 対象外 | atfunded（out_of_scope）、fundingpips（blocked）、trading（own_site） |

ソース: `data/scans/*.json` + `data/help-index/*.json` のみ（ライブフェッチなし）。

### 次のアクション

1. **Page Maker 取込** — 各社 `.pipe.md` を Page Maker に貼付→格納→▶Planタブ生成→全プラン→Hugoエクスポート
2. **verify-firm** — エクスポート後、スラッグ単位でデータ品質チェック
3. **fundingpips 手動確認** — ブラウザで直接アクセスしてコレクション列挙後 normalize-firm 実行

### ファイル変更

- `data/firms/*.pipe.md` — 30件新規作成（commit 49bd664）

---

## 【セッション11・2026-06-10】enumerate-help-index --all 完了

### 作業内容

`enumerate-help-index --all` スキルを完全実行。全33社中32社の `data/help-index/{slug}.json` を生成。

| 状態 | 件数 | ファーム |
|------|------|---------|
| 新規インデックス完了 | 23社 | maven, hantec-trader, nordic-funder, the5ers, fundednext, fundedelite, top-one-trader, fintokei, alpha-capital, e8-markets, blueberry-funded, aquafunded, for-traders, lark-funding, qt-funded, moneta-funded, atmos-funded, finotive-funding, funded-trading-plus, thinkcapital, fxify, hola-prime, fundingpips(blocked) |
| 既存（セッション10完了） | 9社 | city-traders-imperium, ftmo, brightfunded, instant-funding, bem-funding, audacity-capital, trade-the-pool, ment-funding, the-trading-pit |
| out_of_scope | 1社 | atfunded（事業停止） |

### 重要な再分類

| ファーム | 旧分類 | 新分類 | 理由 |
|---------|--------|--------|------|
| the5ers | intercom | wordpress_faq | /collections/ 0件。実態は help.the5ers.com フラットWP構造 |
| funded-trading-plus | intercom | wordpress_faq | help.fundedtradingplus.com は /collections/ 0件。フラットWPナレッジベース |
| qt-funded | intercom | zendesk_or_other_kb | support.qtfunded.com → /hc/en-gb Zendesk構造 |

### ブロック1件

- **fundingpips**: WebFetch 403 + Browser MCP blocked。`fetch_status: "blocked"` で JSON 保存。normalize-firm 時に手動確認要。

### ファイル変更

- `data/help-index/*.json` — 23件新規作成
- `data/help-index/_classification.json` — 全件 `indexed` / `platform` 更新、by_platform 修正、blocked_or_unknown=1

### 次のアクション

1. **`normalize-firm --all`** — `data/help-index/` を参照して `data/firms/{slug}.pipe.md` を生成（Phase 2開始）
2. **fundingpips 手動確認** — ブラウザで直接アクセスしてコレクション列挙

---

## 【セッション10・2026-06-10】データ収集パイプライン基盤

### 追加・変更したファイル（自己説明化＋ヘルプセンター構造化）

| ファイル | 内容 |
|---------|------|
| `data/help-index/_README.md`（新） | ヘルプインデックスの仕様 |
| `data/help-index/_classification.json`（新） | 全33ファームのHelp Center URL+platform分類 |
| `data/help-index/city-traders-imperium.json`（新） | CTI 8コレクション・全52記事の構造 |
| `data/help-index/ftmo.json`（新） | FTMO 60記事フラット構造 |
| `data/plans/city-traders-imperium--1-step.json.draft`（新） | CTI 1-StepプランのDBP_02 22スロット |
| `data/plans/city-traders-imperium--2-step.json.draft`（新） | CTI 2-StepプランのDBP_02 22スロット |
| `data/plans/city-traders-imperium--instant.json.draft`（新） | CTI InstantプランのDBP_02 22スロット |

### 確立したパイプライン

```
data/scans/ (DOM Scanner出力・既存33件)
   + 
data/help-index/ (Help Center構造インデックス・1回きり)
   ↓
LLM正規化スキル `/normalize-firm <slug>` (Phase 2で実装予定)
   ↓
data/firms/{slug}.json.draft  +  data/plans/{firm}--{plan}.json.draft
   ↓ マスター承認
data/firms/{slug}.json  +  data/plans/{firm}--{plan}.json
```

### Help Center分類結果（33社中）

- **intercom系**: 19社（最多。helpcenter.*/help.*/support.*サブドメイン）
- **wordpress_faq系**: 8社（/faq/ /faqs/ パス）
- **zendesk_or_other_kb**: 2社（the-trading-pit, audacity-capital）
- **same_domain_help_path**: 1社（instant-funding）
- **inline_anchor**: 2社（trade-the-pool, ment-funding — 専用ページなし）
- **out_of_scope**: 1社（**atfunded** — 事業停止中）

### CTI正規化の実証結果

ヘルプセンター12記事（Essential Rules & Guidelines）+ プログラム別4記事から、DBP_02の22スロットを以下精度で正規化：
- high confidence: 13項目
- medium confidence: 4項目
- low_or_unknown: 1項目（一貫性ルール明示なし→「無」推定）

**主要発見**: 1-Stepのみmartingale許可、CTI特有balance-based DD、SL 60秒以内必須、Margin Level 150%以下gambling違反、コピー方向制限など、差別化訴求材料を多数抽出。

### 次のアクション候補

- a) 残り30社の help-index articles 列挙（Phase 1b）
- b) `/normalize-firm` スキル設計・実装（Phase 2）
- c) ATFunded を `data/firm-urls.json` から除外検討
- d) inline_anchor（trade-the-pool, ment-funding）の正規化戦略確定

---

## 【セッション10・2026-06-10】リポジトリ自己説明化

### 背景
新セッション開始時にClaudeが構造を毎回探って質問する非効率を解消するため、自己説明型リポジトリ化を実施。

### 追加・変更したファイル

| ファイル | 内容 |
|---------|------|
| `PROJECT_MAP.md`（新） | リポジトリ構造の正本。データフロー・テンプレ対応表・やってはいけない事を集約 |
| `data/firms/_README.md`（新） | Firmデータ仕様・DBP_01スロット |
| `data/plans/_README.md`（新） | Planデータ仕様・DBP_02スロット |
| `themes/pfd/layouts/_README.md`（新） | Hugoテンプレ対応表 |
| `02_docs/_README.md`（新） | ドキュメント一覧 |
| `01_tools/_README.md`（新） | ツール構成 |
| `CLAUDE.md`（更新） | 古い「未実装」記述削除、PROJECT_MAP必読指定、薄く整理 |
| `scripts/record-check.py`（新） | Stop hookで記録もれを検知するスクリプト |
| `.claude/settings.local.json`（更新） | Stop hook 追加（記録チェック自動化） |

### 確立した運用ルール（覆さない）

- **起動時必読順**: `CLAUDE.md` → `PROJECT_MAP.md` → `HANDOFF.md` → メモリ
- **構造の正本**: `PROJECT_MAP.md`（重複させない）
- **進捗・決定の正本**: `HANDOFF.md`（本ファイル）
- **AI用の仕組み整備**: ソートーが選択肢を問わず判断・実装する（メモリ `feedback-autonomy`）
- **Stop hook**: ターン終了時に git status を見て、レイアウト/データ/構造を変更したのに該当ドキュメント未更新ならClaudeに通知

### Git pull で取り込んだもの（リモート→ローカル）

- `.obsidian/` 配下・workspace.json 等の削除（gitignore追加に伴う整理）
- `content/guide/` 3記事（drawdown / consistency / max-loss）
- `content/ranking/payout-speed.md`
- `02_docs/N089-SMC_Daily_Bias_*.md` / `N091-CryptoCompare_API_*.md`
- `02_docs/firm-url-list.md`
- `data/firms/*.json` 約30件の微修正、`data/glossary.json` 大幅更新、`data/pfdb.json` 大幅更新
- `01_tools/core/page-maker-v12.html` 微修正、`PROJECT_HUB.canvas` 更新

---

## 0. プロジェクト概要

- **名称**: Prop Firm Challengers（PFD）
- **技術スタック**: Hugo + Netlify + GitHub
- **旧運用**: Notion × Wraptas（廃棄）
- **作業ディレクトリ**: `D:\vs code\propfirm-database`
- **役割分担**: マスター=戦略立案 / ソートー(Claude)=技術補佐・Hugo実装・フロントエンド

### 関連リソース
- DB_000_Policy: https://www.notion.so/25fcc2b7bd0648559b616222f2ddd355
- DB_100_Impl: https://www.notion.so/21c1182902234c528e5ea45c7dc0a474
- Page Maker 分析: [page-maker-v11-analysis.md](page-maker-v11-analysis.md)

---

## 1. 現在の取り組み（大方針）

**プロップファーム情報サイトのウィジェット（チャート/グラフ/表）を完全静的化して Hugo に載せる。**

### 確定した設計判断（重要・覆さない）

| # | 決定 | 理由 |
|---|---|---|
| ① | **方法A＝完全静的化**。Worker はページ描写に使わない | SEO・速度・運用簡素化 |
| ② | データの通り道は **1本道**：Page Maker → 計算機 → Hugo | データ整合・追跡可能性 |
| ③ | **計算機（Widget Maker）を独立ツール化** | ウィジェットをどんどん追加できる構造にするため |
| ④ | 計算機は **完成SVG/HTMLまで出力**（Hugoは貼るだけ） | Hugoに計算ロジックを持たせない／見た目を完全制御 |
| ⑤ | 計算機の入力は **Page Maker出力JSONのみ**（手入力は試作時の一時措置） | 1本道の徹底 |
| ⑥ | **MASTER_DEFS が唯一の正本**。スロット・用語・キーマップはここから derive | 分散定義の撲滅 |

### 役割（3層）
```
Page Maker（入力・収集） ──出力JSON──▶ Widget Maker（計算+描画） ──完成SVG──▶ Hugo（配信）
```

---

## 2. 成果物（ファイル）

| ファイル | 内容 | 状態 |
|---|---|---|
| `01_tools/page-maker-v11.html` | データ入力・収集ツール | 稼働中（MASTER_DEFS 導入済み） |
| `01_tools/widget-maker.html` | **計算機（新規）**。プラグイン方式でウィジェット生成 | 試作 v0.1 |
| `02_docs/page-maker-v11-analysis.md` | Page Maker 構造分析 | 完了 |
| `02_docs/HANDOFF.md` | 本資料 | 随時更新 |

### Page Maker の正本構造（セッション5で確立）

```
MASTER_DEFS（page-maker-v11.html 内）  ← 唯一の正本
  dbp01[23件]  fkey / id / term / section / hint / definition
  dbp02[23件]  pkey / id / term / section / hint / definition / extra(P02b)
  koryaku[3件] id / term / section / hint
      │
      ├─ SLOT_DEFS        ← UI表示（自動生成）
      ├─ FIRM_KEY_MAP      ← Hugo export（自動生成）
      ├─ PLAN_KEY_MAP      ← Hugo export（自動生成）
      ├─ F_KEY_MAP         ← 取込テーブル解析（自動生成）
      └─ GLOSSARY_SEED     ← Firm項目(F01-F22) + Plan項目(P01-P20+P02b)（自動生成）
                             + GLOSSARY_BASE（表記・計算結果・固定）
```

**変更はすべて MASTER_DEFS の1行のみ。** SLOT_DEFS/GLOSSARY_SEED 等は直接編集禁止。

### Widget Maker の構造（拡張方法）
```js
const WIDGETS = [ PAYOUT_TIMELINE, /* ここに足すだけで増える */ ];
// 各ウィジェット = { id, name, defaultData, calc(data), render(result)→HTML }
```

---

## 3. 進捗（いま どこまで）

### ✅ 完了（〜2026-05-30）

**Page Maker v34（`01_tools/page-maker-v11.html`）**
- `steps` スロット追加（DBP_02 P20）
- ボタン整理: ヘッダーデータ管理ドロップダウン化・縦タブ選択/プロンプトバー統合・個別削除ボタン廃止→選択削除に統一・Plan行チェックボックス追加
- ルールテーブルエディタ（📊テーブル）: DBP-02のrd_*を有無バッジ+プルダウン+数値入力でインライン編集
- クーポン設定生成: DOMスキャナーJSON貼り付け→クーポンセレクター自動抽出
- 貼り付け/取り込みエリア自動開閉

**Hugo サイト実装**
- クーポンサイドバー全ページ組み込み（`baseof.html`）
- FirmカードロゴにGoogle Favicon API適用（トップ・一覧）
- `plans/single.html` を日本語スキーマに全面修正（`.Content`優先・rd_*テーブル対応）
- `plans/single.html` ルーティング修正（`type: plans`追加）
- `/api/index.json` 生成（Hugo→Netlify→クーポンサイドバー）
- `couponPage` URLを `hugo.yaml` params で管理

**クーポン自動化パイプライン**
- DOM Scanner ブックマークレット（`01_tools/Dom scanner BMT`）
- GitHub Actions cron（毎月3日・18日）: Playwright → `data/firms/*.json` 更新 → Netlifyデプロイ
- `data/coupon-config.json`: FundedNext FLEX 設定済み
- `scripts/extract-coupons.mjs`: Playwright実行スクリプト

**Notion MCP接続**
- `.mcp.json` + `@notionhq/notion-mcp-server` で接続確立
- DB_100_Impl から移設・転用タスクを自動取得 → `HANDOFF.md` に整理

---

### ✅ 完了（2026-05-30 セッション3）

**Page Maker ボタン整理**
- Firmリストパネル完成: グ（グループ選択）+ □（Firm名のみ）の2段チェック、プロンプト▾ドロップダウン（リサーチ/ファーム/プラン/攻略/再調査）、選択バー（×解除・コピー・削除）
- 取込エリア: Dom / 自動 / ⇨ / × の4ボタン構成
- ❏小窓ボタン: 貼付エリアタイトル横に配置
- データ▾: CSV一括登録を統合
- トグルスイッチ: Page Makerタイトル横（スロット↔用語）

**クーポン自動化パイプライン強化**
- Dom貼付 → 自動でcoupon-config.jsonに保存
- coupon-config.json スキーマ拡張: `{firmSlug: {coupon: {...}, rules: {...}}}` 構造

---

### ✅ 完了（2026-06-03 セッション4）

**site-scanner → Worker → GitHub パイプライン構築**
- `01_tools/coupon-fetcher/worker.js` — `/scan` POST エンドポイント追加・CORS ヘッダー追加
- `pfd-coupon-fetcher` Worker を Cloudflare にデプロイ済み
  - URL: `https://pfd-coupon-fetcher.purple-voice-a554.workers.dev`
  - Secrets 登録済み: `ANTHROPIC_KEY` / `GITHUB_TOKEN` / `TRIGGER_SECRET=pfd-secret-2026`
- `01_tools/site-scanner.js` — bookmarklet ソース管理ファイル作成（POST直行版）

**未解決: ブックマークレットが無反応**
- Chrome の `allow pasting` セキュリティが邪魔でコンソールテスト未完
- CORS fix 適用後のデプロイは完了済み

---

### ✅ 完了（2026-06-06 セッション5）

**Page Maker 正本（MASTER_DEFS）構築**

- **F21/F22 正式追加**（commit `abf18fc`）
  - GLOSSARY_SEED: F21=プラン名リスト（名称のみ列挙）/ F22=プラン比較テーブル を Firm項目に追加
  - F_KEY_MAP: F21→planList / F22→planComparison に更新（旧: F21→planComparison）
  - リサーチプロンプトの `（F21）` ラベル削除

- **MASTER_DEFS を唯一の正本として導入**（commit `21da4d6`）
  - `MASTER_DEFS`（dbp01/dbp02/koryaku）新設
  - 下記5定義を全て MASTER_DEFS から自動導出:
    - `SLOT_DEFS`（UI表示）
    - `FIRM_KEY_MAP`（Hugo export用）
    - `PLAN_KEY_MAP`（Hugo export用）
    - `F_KEY_MAP`（取込テーブル解析用・ローカル変数）
    - `GLOSSARY_SEED` の Firm項目(F01-F22)・Plan項目(P01-P20+P02b)
  - `GLOSSARY_BASE` を分離（表記・計算結果18+5件の固定エントリ）
  - `buildGlossarySeed()` 関数追加
  - `rd_minDays` ラベル変更（`最低取引日数` → `最低取引日数（合格）`）の後方互換エントリ追加
  - 旧ハードコード定義（SLOT_DEFS/GLOSSARY_SEED直書き等）を全削除

---

### ✅ 完了（2026-06-06 セッション6）

**Page Maker プレビュー機能とデータ格納一元化**（commit `4e5738c`）

- **プレビュー3ページ新設**（公開ページ準拠ダークテーマ）
  - FirmPreview: F01〜F22 + 価格テーブル（テーブル1）を集約表示
  - PlanPreview: 親FirmのpriceTable（該当プラン強調）+ 早見表4列 + ルール詳細リスト形式
  - KoryakuPreview: 3断面（k_dd/k_rules/k_payout）
  - 旧 Markdown プレビューは削除し新プレビューに一本化
- **データ格納一元化（重複削除）**
  - `dbp02.priceTable` スロット削除 — 親Firm.priceTable を正本に統一
  - `dbp02.ruleQuickRef` スロット削除 — 未使用デッドコード
  - `dbp01.priceTable` 汎用スロット欄を MASTER_DEFS から削除 — 価格タブ専用エディタに一本化
  - プラン比較テーブルから価格行を除外（priceTable と重複していた下半分）
  - デッドコード `aiSlotIds` 削除
- **ナビゲーション修正**
  - Plan編集中の Firm/価格/攻略 ボタン → 親Firmへ自動遷移＋該当モード設定
  - Firm編集中の Plan/早見表 ボタン → 先頭Planへ自動遷移
  - `navigateTab(tabId, mode)` ヘルパ追加
- **UI改善**
  - PriceMatrixEditor の行削除「×」ボタンを右端→左端に移動（プラン数増加時に隠れない）
- **プロンプト正本反映**
  - リサーチプロンプト: プラン比較9行の内容を明示・不在表記を「ー」に統一
  - プランプロンプト: 「※有」の詳細記述を「ルール全容を詳細列に書く」に強化
  - 「詳細がルールの正本」原則を明文化（補足ではなく本文として書く）
  - 攻略プロンプト最終チェックリストに「全角括弧」「不在表記区別」追加
  - Firm収集項目から F21/F22（出力物）を除外
- **ソース定義 v08 改訂**（commit `4e5738c`）
  - テーブル5（プラン比較）: 価格行を除外しルール9行のみに
  - テーブル7（早見表）: 5列定義（項目|C|F|差分|詳細）に統合・テーブル8は廃止
- **サイトスキャナーパイプライン強化**（commit `ed2bb4b`）
  - worker.js: `/scan` に LLM抽出（価格＋クーポン）統合・差分計算・firms保存・`/cleanup` 追加
  - site-scanner.js: ローカル価格テーブル蓄積・送信前プレビューパネル・複数ページマージ
- **補助ツール追加**（commit `ed2bb4b`）
  - `01_tools/check-braces.js` — page-maker-v11.html の括弧バランス検査
  - `01_tools/firm-tour.html` — Firm一覧俯瞰ビュー
  - `01_tools/html文章掃除.html` — HTMLテキスト整形ツール
  - `data/firm-urls.json` — スキャン対象URLリスト
  - `data/pfdb.json` — ファームデータ蓄積（+3012行）

---

### ✅ 完了（2026-06-06 セッション7）

**slug 不整合の根治＋全データクリーンアップ**

- **問題特定**: `content/firms/{slug}` ↔ `data/firms/{file}.json` ↔ JSON 内 `firmSlug` の3者で slug が不一致
  - 例: `alpha-capital/` ↔ `alphacapitalgroup.json` ↔ `firmSlug:"alphacapitalgroup"`
  - 原因: 旧 exportHugo 時の firmName 入力が雑だった（"AlphaCapitalGroup" 等の空白なし形）
  - 影響: `firms/list.html:25` の `.slug` 参照 + 個別ページの JSON 引き込みが両方破綻
- **Page Maker の slug 決定ロジック確認**（`page-maker-v11.html:4196`）
  - `const slug = slugify(firmName) || firm.id` の一本道
  - `slugify()` (L185-187): lowercase → 空白→ハイフン → 英数_-以外削除 → ハイフン正規化
  - 期待動作: "Alpha Capital Group" → `alpha-capital-group`
- **全削除実行**（pfdb.json が正本として健全＝tabDataMap 61件・firms 33件保持を確認後）
  - `data/firms/*.json` 34件全削除
  - `data/plans/*.json` 27件全削除
  - `content/firms/*/` 34フォルダ全削除（`_index.md` のみ残存）
  - `content/firms/ftmo.md`（旧スケルトン重複）削除
- **正式名称33件 固定**（`01_tools/firms-bulk-import.csv` 作成）
  - 命名規則: firmName を英語空白区切りの正式名で入力 → slugify で URL生成
  - 主な確定: Alpha Capital Group / Maven Trading / The5ers（%なし）/ Top One Trader 等
  - Page Maker CSV format: `firmName,plan1,plan2,...`（1行1ファーム・カンマ区切り・ヘッダ無し）

---

### ✅ 完了（2026-06-08 セッション8）

**禁止行為(P19)を別シェイプの独立テーブルに分離**（commit `17529d6`）

- データモデル変更: 禁止行為は比較テーブル(C|F|差分|詳細)に収まらないため分離。
  形状 `禁止行為={items:[{行為名,備考,行為,処分}]}`（差分概念廃止・備考は極稀なC/F差異用）
  - MASTER_DEFS.dbp02 には `rd_prohibited` を残置（一括抽出に乗せるため）。撲滅ではなく「別シェイプ型」の一点化
  - ヘルパ `parseProhibit` / `serializeProhibit` / `parseProhibitTable` 追加
- Page Maker: 専用 `ProhibitEditor`（行ごと4フィールド＋追加/削除）/ 取込3経路（全プラン一括・単一テーブル・auto_assign）/ exportHugo / PlanPreview を対応
- 公開ページ `plans/single.html`: 禁止行為早見表（行為名|備考＝ルール早見表の直下）・禁止行為詳細（行為名|行為|処分＝ルール詳細の直下）。旧シェイプデータでも無害
- ソース定義 v09・プロンプト・`preview-mockup.html` を新仕様に改訂、v08 削除
- **一括取込バグ修正**: `### 禁止行為テーブル` 見出しが幽霊プラン化する問題を `splitPlanSections` で解消

**抽出ルール改善・ラベルdrift根治・定義訂正**（commit `67b94f9`）

- 最低取引日数: P02(合格)=Challenge専用 / P02b(出金)=Funded専用とし、各行は自フェーズのみ記述。構造上自明な反対フェーズの打ち消し文を排除
- 利益目標 複数ステップ: 「X% / Y% / Z%」スラッシュ区切り（「1次/2次」ラベル廃止）
- **ラベルdrift根治**: `glossaryItemLines` の Firm項目/Plan項目 を MASTER_DEFS 直参照に変更。
  drift した用語辞典に依存せず prompt→NotebookLM→取込(labelToId)・プレビューのラベルが常に正本一致（ラベル不一致で取込不能だったバグの根治）
- 定義訂正（P07 一貫性ルール / P09 時間制限 / P15 スキャルピング制約）を MASTER_DEFS・ソース定義v09・glossary.json・pfdb.json に反映
- pfdb.json 用語辞典の stale な term/definition（P09/P11/P14）を正本へ再同期（差分0）

> 検証: Page Maker は静的サーバ＋ブラウザでマウント確認・round-trip検証済み。Hugo は本環境で Application Control によりビルド不可のため、公開ページの最終見た目は hugo-dev スキルでマスター側ターミナル確認が必要。

---

### ✅ 完了（2026-06-09 セッション9）

**アフィリエイトURL・クーポンコード スロット追加（DBP_01）**

- `MASTER_DEFS.dbp01` に3スロット追加（`page-maker-v12.html`）。新セクション「アフィリエイト」に配置。
  - `email`（メールアドレス）/ `affiliateUrl`（アフィリエイトURL）/ `couponCode`（クーポンコード）
  - `email` はメール配信クーポン受信用の登録アドレス。Firm⟷アフィリエイトURL⟷メールクーポン（→サイドバーへ流す）を紐づける内部データ。旧 exportHugo のハードコード `fj["メールアドレス"]`（存在しないスロットid参照で常に空だった残骸）を削除し、スロット由来のループ出力に一本化。
  - **意図的に `fkey` 無し** — マスター手入力の内部データであり公式サイトから収集する項目ではないため、LLM収集プロンプト（fkey filter, L458）・定義注入から除外。編集UI表示・JSON出力・キーマップには `MASTER_DEFS` 経由で自動伝播。
- F04 `officialUrl` を「公式URL（正本）」専用に修正（hint/definition から"アフィリエイト優先"を削除し、素の公式URLのみ格納する運用へ分離）。
- 内部データ正本: アフィリエイトURL/クーポン一覧は [firm-url-list.md](firm-url-list.md)（The5ers クーポン `9HFH2XXC` 記録済・Coupon_Code 列新設）。

**既存アフィリエイトデータ充填＋スキーマ正規化（data/firms/*.json 全33件）**

- exportHugo の不具合修正（`page-maker-v12.html` L5463付近）: 新スロット追加で `fj["アフィリエイトURL"]` がループ出力と重複し、直後の旧ハードコード行が空で上書きしていた。旧 `fj["アフィリエイトURL"]=…` と `fj["クーポン"]=[]` の2行を削除し、MASTER_DEFS スロット由来のループ出力に一本化。
- 全 firm JSON のキー `クーポン`(配列・旧箱) → `クーポンコード`(文字列) へ改名統一（昔の紛らわしい箱を撲滅）。
- アフィリエイトURL 充填6社: aquafunded / city-traders-imperium / for-traders / fundedelite / fundingpips / the5ers（出典: [firm-url-list.md](firm-url-list.md)）。The5ers は `クーポンコード` = `9HFH2XXC` も投入。
- 注意: これらは exportHugo 再実行で再生成される。正本運用は Page Maker スロット入力（firm JSON のスロット取込 round-trip で保持）。

**【未実装・次セッション】表示側フォールバック仕様**
- 公開ページの「公式へ」ボタンのリンク先は **`affiliateUrl | default officialUrl`**（アフィリエイト優先、空なら公式URL）。
- 適用先: Hugo `firms/single.html` 実装時（現状レイアウト未実装）。`preview-mockup.html` の「公式サイト →」は現状 `href="#"` プレースホルダ。

---

### ⬜ 次にやること（優先順）

1. **E8 等を新ルールで再抽出 → 一括取込 → 表示確認** — 禁止行為別テーブル・最低取引日数の簡潔文・利益目標スラッシュ・正本ラベルが出るか実機確認
2. **Hugo dev server で禁止行為2テーブルの見た目確認** — `plans/single.html` 禁止行為早見表/詳細のレンダリング（本環境ではHugo実行不可のため未確認）
3. **Page Maker で CSV 一括取込 → 正式 firmName で再構成** — `01_tools/firms-bulk-import.csv` をデータ▾→追加CSVに貼付け
4. **exportHugo 再実行** — クリーンな slug で `data/firms/*.json` / `content/firms/{slug}/_index.md` 再生成
5. **【継続】Obsidian 本格運用** — vault 構造設計・タスク管理プラグイン導入・テンプレ化（公開サイト構造側の整地を優先したため繰越）
6. **ブックマークレット動作確認** — `01_tools/site-scanner.js` 最新版で実機テスト → `data/scans/` に JSON 到達確認
7. ❷ DBP_01 プランナビゲーション（firms/single.html）
8. ❸ 実質最短日数タイムライン（Widget Maker 移植）

---

## 4. 計算ロジック仕様（最速出金スケジュール）

用語辞典（Page Maker内 GLOSSARY_BASE）の計算結果ラベルと一致：
- `CALC_PASS` 最短合格 = 各Step `MAX(最低取引日数, 一貫性達成最速)` の合計。不存在は 1日×Step数 でフォールバック
- `CALC_PAYOUT` 最速出金 = 出金頻度待機を反映（随時0/毎週MAX(7,X)/隔週MAX(14,X)/月次MAX(30,X)）
- `CALC_TOTAL` トータル = 最短合格 + 最速出金

※ 計算ロジックの本体は Page Maker の `generateKoryakuPrompt` 断面③にも文章化済み。

---

## 5. サイト照合タスク（移設・転用リストをHugo実装に落とし込み）

> DB_100_Impl の移設・転用リストを現在の Hugo サイト実装と照合してタスク化。

### ❶ 緊急修正（データ不整合）

- [x] **`plans/single.html` スキーマ修正** — 日本語キー（`利益目標`・`rd_*` 等）に全面差し替え済（セッション3）。早見表＋ルール詳細＋禁止行為2テーブルを描画（セッション8で禁止行為分離対応）

### ❷ データ入力が揃えば実装できるもの

- [x] **DBP_02 ルール早見表＋ルール詳細＋禁止行為テーブル** — plans/single.html に実装済（rd_* を C/F/差分の早見表＋詳細リスト、禁止行為は別シェイプの専用2テーブル）
- [ ] **DBP_01 プランナビゲーション** — firms/single.html に配下プランへのリンク一覧を追加
- [ ] **About Us / フッター整理** — baseof.html のフッターに情報追加、About ページ作成

### ❸ Widget Maker と連携（計算が必要）

- [ ] **実質最短日数タイムラインwidget** — Widget Maker で生成した SVG を plans/single.html の partial として埋め込む（Widget Maker 移植中）
- [ ] **プラン別難易度スコアwidget** — C_Score / F_Score の算出ロジック確立後、firms/single.html に埋め込み
- [ ] **DBP_02 実質最短日数 再計算** — Widget Maker の計算ロジックと PLAN_KEY_MAP の Steps / 出金頻度を結線

### ❹ データ設計が必要（後回し可）

- [ ] **マトリクス図_Challenge難易度スコア** — C_Score × F_Score のデータ算出が前提
- [ ] **難易度チャート（TradingView型 GC/DC）** — 4ベクトル×21項目のスキーマ設計が必要
- [ ] **難易度スキャナー レーダースイープ演出** — スコアデータ確立後
- [ ] **Trailing Drawdown 4Type比較シミュレーター** — 01_tools/ にスタンドアロン追加

### ❺ 01_tools に移設（サイトと独立）

- [ ] **今日のバイアス 暗号資産SMC分析ツール** — 01_tools/ に格納（完成品をそのまま移動）
- [ ] **CryptoCompare API 105銘柄対応** — `01_tools/smc-bias-analyzer.html` を拡張

### ✅ 完了済み

- クーポンログ_右固定サイドバー（baseof.html + GitHub Actions）
- パーマリンク / slug ルーティング（Hugo 標準）
- 用語辞典の表記統一（GLOSSARY_SEED P02/P02b/P20 等）
- SMC Daily Bias 分析ツール（`01_tools/smc-bias-analyzer.html` 存在）

---

## 6. 移設タスク（旧Wraptas/Worker → Hugo）

> 移設 = 旧環境の**具体的ツール・ウィジェット**を Hugo 新環境に移す作業。DB_100_Impl 状態=移設 より自動取得。

- [ ] DBP_01 プランナビゲーション ウィジェット
- [ ] ルール早見表テンプレート＋攻略_本文フロー設計
- [ ] 攻略記事 プラン別難易度スコアwidget v1.0.2 — C_Score/F_Score/Easy-Hardランク表示
- [ ] 攻略記事 タイムラインwidget v1.3.1 — 出金タイムライン棒グラフ
- [ ] 実質最短日数タイムラインwidget（攻略_Firm用） — Widget Maker に移植中
- [ ] 難易度スキャナー レーダースイープ演出
- [ ] DBP_02 ルール詳細テーブル化＋差分強調連動 ver.03
- [ ] DBP_01 スコアチャートwidget（C_Score/F_Score）
- [ ] Trailing Drawdown 4Type比較シミュレーター
- [ ] マトリクス図_Challenge難易度スコア — C_Score × F_Score 2軸マトリクス
- [ ] 難易度チャート（TradingView型 GC/DC） — 4ベクトル×21項目のC/F比較
- [ ] サイト全体デザイン_TradingView風ダークテーマ
- [ ] About Us / 情報提供フォーム / フッター整理
- [ ] クーポンログ_右固定サイドバー ✅ 済（Hugo baseof + GitHub Actions）
- [ ] SMC Daily Bias 分析ツール ver.01 — 01_tools/ に移設
- [ ] CryptoCompare API 105銘柄対応（SMC Daily Bias）
- [ ] 今日のバイアス - 暗号資産SMC分析ツール — 01_tools/ に移設
- [ ] GAS_DB05メール自動登録_Claude API統合版

---

## 7. 転用タスク（考え方・アプローチの流用）

> 転用 = 旧環境のロジック・設計思想を**新しい文脈に応用**する。DB_100_Impl 状態=転用 より自動取得。

- [ ] 縦タブプロンプトボタン修正（DBP_01/DBP_02）— Page Maker の UI設計をHugo側スロット構造に転用
- [ ] 最低取引日数 表記統一 ver.01 — C系「最低取引日数（合格）」/F系「最低取引日数（出金）」→ MASTER_DEFS で正本化済み ✅
- [ ] 統制語彙統一・P1-P3クリーンアップ ver.01 — 不在表記ルール → `GLOSSARY_BASE` の notation に転用済み ✅
- [ ] 汎用デザインエディタ（スタンドアロンHTMLツール）→ Page Maker / Widget Maker のテーマ設計に転用
- [ ] パーマリンク実装（slugプロパティ追加）→ Hugo の slug ルーティング設計に転用済み ✅
- [ ] DBP_02 ルール詳細静的化（SEO対策）→ Hugo テンプレートでのルール表静的生成に転用
- [ ] DBP_02 実質最短日数 再計算・Worker v7対応 → Widget Maker の計算ロジックに転用中

---

## 8. プロンプト正本反映（✅ 完了 セッション5〜6）

MASTER_DEFS/GLOSSARY_BASE への動的参照化が全箇所完了。ヘルパ関数（`ddTypesCount` / `ddTypesStr` / `diffTermLine` / `freqCalcLines` / `calcColNames`）と `glossaryRulesBlock` / `glossaryItemLines` 経由で全プロンプトが用語辞典を単一情報源として参照する設計が確立。

---

## 9. 【次セッション・別チャット】Obsidian 本格運用

> Notion を Page Maker（構造化データ）と Obsidian（非構造ナレッジ）の2軸で完全代替する構想。
> Page Maker 側はすでに正本管理・プレビュー・用語辞典動的注入で Notion を超えている。
> 残るは Obsidian 側の運用基盤整備。

### 構想

```
Page Maker v11        ← 構造化データ正本（JSON→Hugo直結）
Obsidian             ← 非構造ナレッジ（メモ・タスク・設計・用語議論）
```

### Obsidian 担当領域

| Notionで担っていた役割 | Obsidian での実現方法 |
|---|---|
| ナレッジ蓄積（用語・調査メモ・気付き） | `zz_notes/` 配下に Markdown・タグ・双方向リンク |
| タスク管理（DB_100_Impl） | Tasks プラグイン or `02_docs/HANDOFF.md` のチェックボックス |
| 設計ドキュメント（ポリシー・引き継ぎ） | `02_docs/` 配下に Markdown（gitで履歴管理） |
| 用語辞典の議論・草案 | Obsidian で議論 → 確定したら Page Maker `GLOSSARY_BASE` へ反映 |

### Obsidian 側でやること（次セッション）

1. **vault 構造設計** — フォルダ階層・命名規則・テンプレ
2. **必須プラグイン導入** — Tasks / Dataview / Templater / Git
3. **テンプレート作成** — ファーム調査メモ・用語議論・タスク票
4. **既存 HANDOFF.md と整合** — Obsidian で開いたときに自然に読める構造に
5. **MOC（Map of Content）構築** — トピック横断のナビゲーションノート

---

## 10. 留意点・補足

- Page Maker はファイル名「v11」だが内部表記は `APP_VERSION="v0.9"`（不一致・混乱注意）
- LLM呼び出しは Cloudflare Worker プロキシ `/api/llm` 経由（APIキーは Worker Secrets に隔離）
- 旧 Worker (PFC API v22) の `generateWidgetHtml` は価格カード/スコアチャート/ルール表を生成していた → **これらを Widget Maker に移植していく**（最速出金スケジュールは旧Workerには無く新規）
- Hugo出力（Page Makerの🚀Hugoボタン）は File System Access API依存＝Chromium系ブラウザ必須
- `GLOSSARY_SEED` は `buildGlossarySeed(MASTER_DEFS, GLOSSARY_BASE)` で生成。`GLOSSARY_BASE` のみ直接編集可
- `rd_minDays` の UI ラベルが `最低取引日数（合格）` に変更済み。旧ラベル `最低取引日数` の後方互換エントリ（labelToId）あり
