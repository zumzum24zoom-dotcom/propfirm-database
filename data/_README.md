# data/ — 公開層（Hugoビルド入力の正本）

> **このフォルダには公開サイトに出るデータだけを置く。** Hugoは `data/` 配下の全JSONを `hugo.Data.*` として無条件ロードするため、ドラフト・収集生データ・状態ファイルを混ぜると公開層を汚す。作業中間物は `_work/` へ（2026-06-14・設計判断#12）。

## 中身（これ以外を増やさない）

| パス | 役割 | Hugo |
|------|------|------|
| `firms/{slug}.json` | Firm本体（DBP_01）。1社1ファイル | `Data.firms` で描画 |
| `plans/{firm}--{plan}.json` | Plan本体（DBP_02）。1プラン1ファイル | `Data.plans` で描画（設計判断#11） |
| `glossary.json` | 用語辞典（Page Maker出力） | ビルド入力 |
| `coupon-config.json` | クーポンセレクター設定（DOM Scanner出力） | ビルド入力 |

## ルール

- **正本はここ。** スロット定義の正本は Page Maker 内 `MASTER_DEFS`。
- `glossary.json` は手編集禁止（Page Maker から再エクスポート）。
- ドラフト・統合DB・収集生データ・URLレジストリ・進捗は `_work/` に置く（[_work/_README.md](../_work/_README.md)）。
- データフローの全体像は `PROJECT_MAP.md` §2。
