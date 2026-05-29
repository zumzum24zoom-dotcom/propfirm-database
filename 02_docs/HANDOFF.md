# 引き継ぎ資料 — Prop Firm Challengers / propfirm-database

> **運用ルール**: このファイル1枚を上書き更新する。セッション開始時はまずこれを読む。
> **最終更新**: 2026-05-29

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

### ✅ 完了
- 設計方針の確定（上記①〜⑤）
- Widget Maker v0.1 試作（単一HTML + React + Babel、Page Makerテーマ流用）
- **第1ウィジェット「最速出金スケジュール（PROFIT TIMELINE）」** の計算＋描画を実装
  - 計算: 最短合格 = Σ各Step最低取引日数 / 最速出金 = MAX(頻度待機, 出金最低日数) / トータル = 合算
  - 頻度待機: 随時0 / 毎週7 / 隔週14 / 月次30
  - 描画: ダークテーマのガント横棒（青=Challenge各Step、オレンジ=Funded）、目盛0〜20+

### 🔄 確認中
- 最速出金スケジュールの**見た目が画像（マスター提示）と一致するか**のレビュー待ち

### ⬜ 次にやること
1. **見た目OK確認後** → 作業4: Page Maker に素データ項目を追加（**1本道の実配線**）
   - 追加項目: Steps / 最低取引日数(出金) / 出金頻度 / 着金目安
   - 追加先: `SLOT_DEFS.dbp02` ＋ `PLAN_KEY_MAP`（Hugo出力スキーマ）
2. 作業5: 生成SVGを Hugo の partial/content に配置
3. 以降: 第2第3ウィジェット（スコアチャート / ルール表 / 価格カード）を Widget Maker に追加

---

## 4. 計算ロジック仕様（最速出金スケジュール）

用語辞典（Page Maker内 GLOSSARY）の計算結果ラベルと一致：
- `CALC_PASS` 最短合格 = 各Step `MAX(最低取引日数, 一貫性達成最速)` の合計。不存在は 1日×Step数 でフォールバック
- `CALC_PAYOUT` 最速出金 = 出金頻度待機を反映（随時0/毎週MAX(7,X)/隔週MAX(14,X)/月次MAX(30,X)）
- `CALC_TOTAL` トータル = 最短合格 + 最速出金

※ 計算ロジックの本体は Page Maker の `generateKoryakuPrompt` 断面③にも文章化済み。

---

## 5. 留意点・補足

- Page Maker はファイル名「v11」だが内部表記は `APP_VERSION="v0.9"`（不一致・混乱注意）
- LLM呼び出しは Cloudflare Worker プロキシ `/api/llm` 経由（APIキーは Worker Secrets に隔離）
- 旧 Worker (PFC API v22) の `generateWidgetHtml` は価格カード/スコアチャート/ルール表を生成していた → **これらを Widget Maker に移植していく**（最速出金スケジュールは旧Workerには無く新規）
- Hugo出力（Page Makerの🚀Hugoボタン）は File System Access API依存＝Chromium系ブラウザ必須
