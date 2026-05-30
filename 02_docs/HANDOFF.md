# 引き継ぎ資料 — Prop Firm Challengers / propfirm-database

> **運用ルール**: このファイル1枚を上書き更新する。セッション開始時はまずこれを読む。
> **最終更新**: 2026-05-30（セッション3）

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

### 役割（3層）
```
Page Maker（入力・収集） ──出力JSON──▶ Widget Maker（計算+描画） ──完成SVG──▶ Hugo（配信）
```

---

## 2. 成果物（ファイル）

| ファイル | 内容 | 状態 |
|---|---|---|
| `01_tools/page-maker-v11.html` | データ入力・収集ツール（既存・3217行） | 稼働中 |
| `01_tools/widget-maker.html` | **計算機（新規）**。プラグイン方式でウィジェット生成 | 試作 v0.1 |
| `02_docs/page-maker-v11-analysis.md` | Page Maker 構造分析 | 完了 |
| `02_docs/HANDOFF.md` | 本資料 | 随時更新 |

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

**CLAUDE.md 更新**
- 起動時アクションに `02_docs/HANDOFF.md` 必読を追加

**git コミット（2件）**
- `27f1f5c`: Page Maker強化・Hugo実装・クーポン自動化システム構築（26ファイル）
- `3bf064f`: データ更新・不要ファイル削除
- `35190a4`: 起動時アクション更新・セッション記録

---

### ✅ 完了（2026-05-30 セッション3）

**Page Maker ボタン整理**
- Firmリストパネル完成: グ（グループ選択）+ □（Firm名のみ）の2段チェック、プロンプト▾ドロップダウン（リサーチ/ファーム/プラン/攻略/再調査）、選択バー（×解除・コピー・削除）
- 取込エリア: Dom / 自動 / ⇨ / × の4ボタン構成
- ❏小窓ボタン: 貼付エリアタイトル横に配置
- データ▾: CSV一括登録を統合
- トグルスイッチ: Page Makerタイトル横（スロット↔用語）

**クーポン自動化パイプライン強化**
- Dom貼付 → 自動でcoupon-config.jsonに保存（フォルダ未選択時は自動ピッカー起動）
- toast通知（右下に保存結果表示）
- Firm選択中にDom貼付 → slug自動設定・モーダル不要
- coupon-config.json スキーマ拡張: `{firmSlug: {coupon: {...}, rules: {...}}}` 構造に変更（将来のルール変更検知等に対応）
- extract-coupons.mjs: 新スキーマ対応（`firmEntry.coupon` のみ処理）

### ⬜ 次にやること（優先順）
→ 詳細は「セクション5 サイト照合タスク」を参照

1. ❷ DBP_02 ルール詳細テーブル（plans/single.html）— データ入力後すぐ表示可
2. ❷ DBP_01 プランナビゲーション（firms/single.html）
3. ❸ 実質最短日数タイムライン（Widget Maker 移植）
4. Page Maker でデータ入力継続 → exportHugo

---

## 4. 計算ロジック仕様（最速出金スケジュール）

用語辞典（Page Maker内 GLOSSARY）の計算結果ラベルと一致：
- `CALC_PASS` 最短合格 = 各Step `MAX(最低取引日数, 一貫性達成最速)` の合計。不存在は 1日×Step数 でフォールバック
- `CALC_PAYOUT` 最速出金 = 出金頻度待機を反映（随時0/毎週MAX(7,X)/隔週MAX(14,X)/月次MAX(30,X)）
- `CALC_TOTAL` トータル = 最短合格 + 最速出金

※ 計算ロジックの本体は Page Maker の `generateKoryakuPrompt` 断面③にも文章化済み。

---

## 5. サイト照合タスク（移設・転用リストをHugo実装に落とし込み）

> DB_100_Impl の移設・転用リストを現在の Hugo サイト実装と照合してタスク化。

### ❶ 緊急修正（データ不整合）

- [ ] **`plans/single.html` スキーマ修正** — 旧英語キー（`$plan.account_size` 等）を Page Maker 出力の日本語キー（`利益目標`・`rd_*` 等）に全面差し替え。現状でプランページは何も表示されない

### ❷ データ入力が揃えば実装できるもの

- [ ] **DBP_02 ルール詳細テーブル** — plans/single.html に `rd_*` スロットを Challenge / Funded / 差分の3列テーブルで表示（転用: 旧ルール表ウィジェットのロジック）
- [ ] **DBP_01 プランナビゲーション** — firms/single.html に配下プランへのリンク一覧を追加
- [ ] **ルール早見表** — plans/single.html に `ruleQuickRef` スロットを表示
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

## 6. 転用タスク（考え方・アプローチの流用）

> 転用 = 旧環境のロジック・設計思想を**新しい文脈に応用**する。DB_100_Impl 状態=転用 より自動取得。

- [ ] 縦タブプロンプトボタン修正（DBP_01/DBP_02）— Page Maker の UI設計をHugo側スロット構造に転用
- [ ] 最低取引日数 表記統一 ver.01 — C系「最低取引日数（合格）」/F系「最低取引日数（出金）」→ 用語辞典正本に転用済み
- [ ] 統制語彙統一・P1-P3クリーンアップ ver.01 — 不在表記ルール → `GLOSSARY_SEED` の notation に転用
- [ ] 汎用デザインエディタ（スタンドアロンHTMLツール）→ Page Maker / Widget Maker のテーマ設計に転用
- [ ] パーマリンク実装（slugプロパティ追加）→ Hugo の slug ルーティング設計に転用済み
- [ ] DBP_02 ルール詳細静的化（SEO対策）→ Hugo テンプレートでのルール表静的生成に転用
- [ ] DBP_02 実質最短日数 再計算・Worker v7対応 → Widget Maker の計算ロジックに転用中

---

## 7. 留意点・補足

- Page Maker はファイル名「v11」だが内部表記は `APP_VERSION="v0.9"`（不一致・混乱注意）
- LLM呼び出しは Cloudflare Worker プロキシ `/api/llm` 経由（APIキーは Worker Secrets に隔離）
- 旧 Worker (PFC API v22) の `generateWidgetHtml` は価格カード/スコアチャート/ルール表を生成していた → **これらを Widget Maker に移植していく**（最速出金スケジュールは旧Workerには無く新規）
- Hugo出力（Page Makerの🚀Hugoボタン）は File System Access API依存＝Chromium系ブラウザ必須
