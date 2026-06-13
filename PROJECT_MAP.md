# PROJECT_MAP — propfirm-database

> **これは新セッションのClaudeが最初に読む地図。** 物理構造・データフロー・どこに何があるかを1枚に集約。
> 詳細は各フォルダの `_README.md` を見る。本ファイルはインデックス。
> **更新ルール**: 構造変更・新フォルダ追加時に必ず更新。`HANDOFF.md` は進捗の正本、本ファイルは構造の正本。

---

## 1. プロジェクト概要

- **名称**: Prop Firm Challengers (PFD)
- **目的**: プロップファーム情報サイトの完全静的化（旧 Notion×Wraptas → Hugo）
- **技術**: Hugo + Netlify + GitHub
- **役割**: マスター=戦略 / ソートー(Claude)=Hugo実装・フロント・ツール補佐

---

## 2. データフロー（1本道）

```
Page Maker (01_tools/core/page-maker-v12.html)
    │ 入力・収集（MASTER_DEFS が唯一の正本）
    ▼
data/firms/*.json  +  data/plans/*.json  +  data/glossary.json
    │ Hugo build
    ▼
content/firms/{slug}/ + content/plans/{slug}.md  (描画される)
    │
    ▼
Widget Maker (01_tools/core/widget-maker.html)
    │ data/*.json → SVG/HTML 生成
    ▼
Hugo に貼る（計算ロジックは持たせない）
```

**絶対ルール**
- データの正本は `data/firms/`, `data/plans/`, `data/glossary.json`
- スロット定義の正本は Page Maker 内 `MASTER_DEFS`
- Hugoテンプレは表示のみ。計算しない

---

## 3. ディレクトリ地図

### Hugo領域（規約強制・動かせない）

| パス | 役割 | 詳細 |
|------|------|------|
| `content/firms/{slug}/` | Firmページのコンテンツ | `index.md` + 場合により `_index.md` |
| `content/firms/{slug}/plans/` | プラン子ページ | 旧構造（移行中？要確認） |
| `content/plans/{slug}.md` | Planページ（独立） | 現行の正規パス |
| `content/guide/*.md` | 用語解説記事 | drawdown / consistency / max-loss |
| `content/ranking/*.md` | ランキング記事 | payout-speed 等 |
| `content/api/_index.md` | API出力用ダミー | `/api/index.json` 生成 |
| `data/firms/*.json` | Firm本体データ（DBP_01の22スロット） | `_README.md`参照 |
| `data/plans/*.json` | Plan本体データ（DBP_02の22スロット） | ファイル名 `{firm}--{plan}.json` |
| `data/glossary.json` | 用語辞典（GLOSSARY_SEED + BASE） | Page Maker出力 |
| `data/pfdb.json` | 統合DB（書き出し用） | |
| `data/coupon-config.json` | クーポンセレクター設定 | DOM Scanner出力 |
| `data/firm-urls.json` | ファームURL一覧 | |
| `themes/pfd/layouts/` | Hugoテンプレート | `_README.md`参照 |
| `themes/pfd/static/css/style.css` | スタイル本体 | |
| `static/` | 直接配信される静的ファイル | |
| `hugo.yaml` | Hugo設定（baseURL, theme, params） | |
| `netlify.toml` | Netlifyビルド設定 | |
| `public/` | Hugo出力（gitignore推奨） | |

### 非Hugo領域（自由）

| パス | 役割 |
|------|------|
| `01_tools/core/` | Page Maker / Widget Maker 等 中核ツール |
| `01_tools/coupon/` | クーポン関連（DOM Scanner等） |
| `01_tools/analysis/` | 分析系ツール |
| `01_tools/chat/` | チャット系 |
| `01_tools/utils/` | ユーティリティ |
| `01_tools/launcher/` | 自作HTMLランチャー（port 8765 / ELECOMボタン起動想定） |
| `01_tools/_archive/` | 旧バージョン保管 |
| `02_docs/` | 全ドキュメント（HANDOFF, 分析レポート, ブリーフ）。`_proposal` 接尾辞=構想・未実装 / なし=実装済み正本 |
| `99_chat-tree/` | Obsidian会話ログ（自動生成） |
| `zz_notes/` | Obsidian Base / 雑メモ |
| `data/price-collect/` | 価格テーブル収集生データ（`{firm}_price.md`）。`wide/` に Page Maker取込用の横持ち変換結果 |
| `scripts/` | Node.js スクリプト（クーポン抽出・価格テーブル変換/検証等）。共通処理は `scripts/lib/` |
| `PROJECT_HUB.canvas` / `PROJECT_HUB_v2.canvas` | Obsidian Canvas プロジェクトハブ |
| `start-server.bat` | 加工ツール用ローカルサーバー起動（port 8080）。Canvas の🚀ボタンから起動 |
| `01_tools/launcher/start.vbs` | ランチャー起動（port 8765・コンソール非表示）。ELECOMトラックボール等の1ボタン起動先 |

---

## 4. Hugoテンプレ ↔ コンテンツ対応表

| URL | テンプレ | コンテンツ | データ |
|------|----------|------------|--------|
| `/` | `_default/list.html`（home） | - | - |
| `/firms/` | `firms/list.html` | `content/firms/_index.md` | `data/firms/*.json` 一覧 |
| `/firms/{slug}/` | `_default/single.html` または `firm/single.html` | `content/firms/{slug}/index.md` | `data/firms/{slug}.json` |
| `/plans/` | `plans/list.html` | `content/plans/_index.md` | `data/plans/*.json` 一覧 |
| `/plans/{slug}/` | `plans/single.html` | `content/plans/{slug}.md` | `data/plans/{slug}.json` |
| `/guide/{slug}/` | `_default/single.html` | `content/guide/{slug}.md` | - |
| `/ranking/{slug}/` | `_default/single.html` | `content/ranking/{slug}.md` | `data/*.json` 集計 |
| `/api/index.json` | `api/list.json` | `content/api/_index.md` | `data/firms/*.json` JSON出力 |

**注**: `themes/pfd/layouts/firm/list.html`（単数）が存在するが用途要確認。

---

## 5. 重要ファイル — 直接参照すべきもの

| ファイル | 何のため |
|----------|----------|
| `CLAUDE.md` | 役割・指示形式・起動時アクション |
| `PROJECT_MAP.md` | **本ファイル**（構造の正本） |
| `02_docs/HANDOFF.md` | 現在地（進捗・設計判断）の正本（毎セッション読む。常に上書き） |
| `02_docs/HANDOFF_archive.md` | 過去セッションログ・旧仕様。通常は読まない |
| `02_docs/page-maker-v11-analysis.md` | Page Maker詳細仕様 |
| `02_docs/用語辞典キー設計_v1.md` | glossary構造 |
| `02_docs/計算定義_v1.md` | Widget Maker計算式定義 |
| `01_tools/core/page-maker-v12.html` | MASTER_DEFS（スロット正本） |

---

## 6. やってはいけないこと

- `data/glossary.json` を手で編集する（Page Maker から再エクスポート）
- スロット定義を Hugo テンプレ内に書く（MASTER_DEFS から参照）
- `_archive/` の旧ファイルを current として扱う
- `public/` を編集する（Hugo再生成で消える）
- `99_chat-tree/` を手動編集（Obsidian自動生成）

---

## 7. 新セッション開始フロー

1. `CLAUDE.md` を読む（役割・形式）
2. **本ファイル**を読む（構造把握）
3. `02_docs/HANDOFF.md` を読む（進捗・未解決）
4. メモリ `MEMORY.md` を読む（マスター個別の好み）
5. マスター指示を待つ

---

## 8. 更新履歴

- 2026-06-10: 初版作成（リポジトリ自己説明化の起点）
- 2026-06-11: `01_tools/launcher/` 追加（自作ランチャー / port 8765 / ELECOMボタン起動想定）
- 2026-06-12: `data/price-collect/`・`scripts/lib/` 追加（価格テーブル変換/検証パイプライン）
- 2026-06-14: `03_intake/` 削除（v1ワークフロー遺物。v2では `data/scans/`→`data/firms-v2/` が役割を継承）。ルート重複 `preview-mockup.html` 削除（正本は `01_tools/core/`）
