# 01_tools/

**ローカル単体動作するツール群。ブラウザで開いて使う。**

## 構成

| パス | 内容 |
|------|------|
| `core/` | 中核ツール（Page Maker v12 / Widget Maker） |
| `coupon/` | クーポン関連（DOM Scanner / 抽出ツール） |
| `analysis/` | 分析系ツール |
| `chat/` | チャット系ツール |
| `utils/` | ユーティリティ（小物） |
| `launcher/` | 自作HTMLランチャー（port 8765・ELECOM 1ボタン起動想定）。詳細は `launcher/_README.md` |
| `_archive/` | 旧バージョン保管（参照のみ） |
| `node_modules/` | スクリプト用依存（gitignoreで除外推奨） |

## 中核ツール

| ファイル | 役割 |
|----------|------|
| `core/page-maker-v12.html` | データ入力・MASTER_DEFS正本・Hugoエクスポート |
| `core/widget-maker.html` | data/*.json → 完成SVG/HTML 生成 |

## 使い方

- 単体HTMLとしてブラウザで開く
- LLM呼び出しが必要なものは Cloudflare Worker プロキシ `/api/llm` 経由
- ファイル書き出しは File System Access API（Chromium系専用）
- 旧版は `_archive/` へ移動、削除しない

## 注意

- `core/` 以外のツールは小回り用途。設計判断は `core/` に集約
- ツール追加時は本READMEに1行追加
