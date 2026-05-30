# Page Maker v11 分析レポート

- **対象ファイル**: `01_tools/page-maker-v11.html`（全3217行）
- **構成**: 単一HTML / React 18 + Babel standalone（CDN）/ `type="text/babel"` でブラウザ内JSXトランスパイル
- **内部バージョン表記**: `APP_VERSION = "v0.9"`（タイトルも v0.9）
- **注意**: ファイル名の v11 と内部表記 v0.9 が不一致
- **分析日**: 2026-05-29

---

## 1. UI構造（3カラム + パネル）

| 領域 | コンポーネント | 役割 |
|---|---|---|
| 左カラム | `VerticalTabs` | Firm→Plan階層タブ。＋追加 / CSV一括 / リネーム(ダブルクリック) / 📌ピン留め / ⤵Firm統合 / Firm・Plan両方にチェックボックス。統合アクションバー（未選択+Firm選択中→📋📤📝プロンプト / 選択時→コピー・📄Plan出力・削除）。個別×削除ボタンなし（選択→削除のみ） |
| 中央上 | `PastePanel` | 貼付エリア。テキスト/画像OCR(Claude vision)・保管(アーカイブ)・翻訳・反映。小窓(❏)・早見表(▦)起動 |
| 中央下 | `TargetPanel` | 取込エリア。「自動」=Claude APIでスロット自動振り分け / ＋でスロット格納 |
| 右カラム | `SlotPanel` | テンプレ切替(DBP_01/DBP_02/攻略)。スロット格納・編集・整形(merge)・🔒ロック・MDコピー |
| 右端 | `GlossaryPanel` | 用語辞典(63キー正本)。インライン編集・AI登録・CSV/JSON入出力 |
| モーダル | `EditModal` / `ReinvestigateModal` / `NotionItemSelectModal` / `NotionPreviewModal` | 編集・再調査プロンプト・Notion項目選択・本文プレビュー |
| 別窓 | `__pfmPasteWindowHTML` | 貼り付け小窓(postMessage連携・URL欄・OCR・翻訳) |
| 共通 | `useResize` / `ResizeHandle` | カラム幅・高さドラッグ調整 |

---

## 2. データ入力フィールド一覧

### Firm用（DBP_01 / 22スロット）— `SLOT_DEFS.dbp01`

| セクション | フィールド |
|---|---|
| 基本情報 | firmName / country / established / officialUrl / firmCategory / japanChat |
| 特色 | firmPitch / rewardProgram / scaleUp |
| 取引環境 | broker / platform / serverTime / ddReset / leverage / commission |
| 入出金 | paymentMethods / payoutMethods / payoutPolicy / profitSplit / profitSplitNote |
| 全プラン | planComparison / planList |

### Plan用（DBP_02 / 23スロット）— `SLOT_DEFS.dbp02`

| セクション | フィールド |
|---|---|
| タイトル/価格/早見表 | challengeName / **steps** / priceTable / ruleQuickRef |
| 詳細(rd_*) | rd_target, rd_minDays, rd_dailyLoss(+Type), rd_maxLoss(+Type), rd_consistency, rd_profitCap, rd_timeLimit, rd_news, rd_weekend, rd_overnight, rd_ea, rd_copyTrade, rd_scalping, rd_stopLoss, rd_risk, rd_maxPosition, rd_prohibited |

### 攻略（koryaku / 3スロット）

- `k_dd`（断面① Drawdown） / `k_rules`（断面② 取引ルール） / `k_payout`（断面③ 出金までの流れ）

---

## 3. テンプレートロジック（HTML生成方式）

| 機構 | 内容 |
|---|---|
| データ構造 | `firms[]`（id/name/plans/pinned）＋ `tabDataMap[id]`（slotData/targetText/templateMode）。slotDataは**断片配列**で、`merged:true`断片を優先表示 |
| AI連携 | 全LLMは **Cloudflare Workerプロキシ** (`/api/llm`) 経由（v33でAPIキー直書き廃止）。`claude-sonnet-4-20250514` 使用。429リトライ最大3回 |
| 自動振り分け | 取込テキスト→Claude APIで各スロットへ自動格納（ロック済みスキップ） |
| 整形(merge) | 複数断片→Claude APIで1文に統合 |
| プロンプト生成 | `generateResearchPrompt` / 出力 / `generateKoryakuPrompt`。**用語辞典(GLOSSARY)を単一情報源**として `glossaryRulesBlock` / `glossaryItemLines` で動的注入 |
| 整合性 | マージ取込(`planMerge` / `reidFirm`)・Firm統合(`mergeSlotData`)・localStorageバックアップ(最大30件) |

---

## 4. 出力形式

| 出力 | 形式 | 詳細 |
|---|---|---|
| MDコピー | Markdown | `exportMD`。テンプレ全体をMarkdown見出し+テーブル化 |
| Notion出力 | Markdown/TSV | `generateNotionBody`。項目選択式。ルール詳細はMarkdownテーブル(`\|項目\|Challenge\|Funded\|`) |
| プロンプト | テキスト | クリップボードコピー（NotebookLM/攻略記事用） |
| 全保存/読込 | JSON | `{firms, tabDataMap, glossaryTerms}` |
| 🚀Hugo出力 | JSON + Markdown | `exportHugo`。File System Access API(`showDirectoryPicker`)で実フォルダへ直接書込：<br>・`data/firms/{slug}.json`（FIRM_KEY_MAPで日本語キー化）<br>・`data/firms/{slug}/plans/{planSlug}.json`（PLAN_KEY_MAP）<br>・`content/firms/{slug}/index.md`（front matter付）<br>・`data/glossary.json` |
| 用語辞典 | CSV/JSON | 用語名,カテゴリ,定義,説明,豆知識 |

---

## 5. スタイル・カラー

| 用途 | 変数 | 値 |
|---|---|---|
| 背景 | bg / surface / surfaceAlt | `#0a0e17` / `#111827` / `#1a2332` |
| ボーダー | border / borderLight | `#1e2d3d` / `#2a3a4d` |
| アクセント(緑) | accent | `#00d4aa` |
| 警告/強調 | yellow / red | `#f0b90b` / `#ef4444` |
| 補助色 | blue / purple / green | `#3b82f6` / `#a78bfa` / `#22c55e` |
| テキスト | text / textBright / textDim | `#c8d6e5` / `#e2e8f0` / `#636e7b` |
| フォント | font | `JetBrains Mono / Fira Code`（本文は Noto Sans JP） |

**セクション色マップ(`SEC_COLORS`)**: 基本情報=緑 / 特色=紫 / 取引環境=青 / 入出金=緑 / 全プラン・詳細=黄 / DD・断面=赤。ダークターミナル風UI。

---

## 補足・所見

- ファイル名 **v11** と内部 **v0.9** 表記が不一致（管理上の混乱要因）
- LLMキーはWorker Secrets（`env.ANTHROPIC_KEY`）に隔離済み（v33でハードコード全廃）
- 用語辞典64キー（Firm20 / Plan21 / 表記18 / 計算結果5）が表記ルールの正本として全プロンプトに動的注入される設計
- Hugo出力は File System Access API 依存のため Chromium系ブラウザが必要
