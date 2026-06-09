# themes/pfd/layouts/

**Hugoテンプレート本体。フォルダ名は Hugo の規約に従う（変えられない）。**

## 構成

| パス | 描画対象 |
|------|----------|
| `_default/baseof.html` | 全ページ共通の `<html><head><body>` 骨格（サイドバー等含む） |
| `_default/list.html` | デフォルト一覧（home / 未定義sectionのフォールバック） |
| `_default/single.html` | デフォルト詳細（guide, ranking, firms/{slug}等） |
| `firms/list.html` | `/firms/` 一覧（カードグリッド） |
| `firm/list.html` | **用途要確認**（単数形、Hugo規約外） |
| `plans/list.html` | `/plans/` 一覧 |
| `plans/single.html` | `/plans/{slug}/` 詳細（rd_*テーブル含む） |
| `api/list.json` | `/api/index.json` 出力（クーポンサイドバー等が消費） |

## Hugo の探索順

詳細ページ `/foo/bar/` の場合:
1. `layouts/foo/single.html`
2. `layouts/_default/single.html`
3. baseof は最後にラップ

## 重要な約束

- **計算ロジックを持たせない**（Widget Maker側で完成HTMLを生成して貼る）
- データ参照は `.Site.Data.firms` / `.Site.Data.plans` 経由
- スロット定義はテンプレ内にハードコードしない（MASTER_DEFS が正本）
- 用語は `data/glossary.json` から引く

## デザイントークン

色・フォントは `themes/pfd/static/css/style.css` のCSS変数で集中管理。Page Maker分析（`02_docs/page-maker-v11-analysis.md`）にトークン一覧あり。
