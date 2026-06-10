# 01_tools/launcher/

**自作ランチャー。1ボタン起動 → ポップアップ窓 → ツール一覧 / 追加 / 編集 / 削除。**

## 構成

| ファイル | 役割 |
|----------|------|
| `start.vbs` | ELECOMボタン等から呼ぶ入口。コンソール窓を出さずに start.bat を起動 |
| `start.bat` | port 8765 で `serve.py` を起動 + Edge/Chrome を `--app` モードで開く |
| `serve.py` | カスタム HTTP サーバ。`GET /api/tools` と `POST /api/tools` で tools.json を読み書き。静的配信はリポジトリルート起点 |
| `index.html` | ポップアップUI（検索・カテゴリ別表示・行クリック起動・⋯から編集・＋から追加） |
| `tools.json` | ツール登録（永続データ） |

## 設計のポイント

- **Edge `--app` モード** で開くのでタブ・URLバーなしの**独立ポップアップ窓**になる
- Edge 不在なら Chrome、両方無ければ既定ブラウザにフォールバック
- 専用 user-data-dir（`%LOCALAPPDATA%\PFDLauncher\edge-profile`）で通常Edgeと**プロファイル分離**
- ウィンドウサイズ: `520x760`（縦長ポップアップ）
- サーバルート = **リポジトリルート** → tools.json の path は `/01_tools/core/xxx.html` のような絶対パス
- `start.bat` は `%~dp0` で自身位置から相対起動 → **自宅/職場でクローン先パスが違っても動く**
- 多重起動防止: `netstat` で 8765 LISTENING を検知したらサーバは起こさず Edge だけ開く
- バックグラウンドサーバは `pythonw` で起動 → 黒い窓は一切出ない

## 起動方法

### ELECOMトラックボール（推奨）
マウスアシスタント → 空きボタン → **「ファイルを指定して実行」** → `start.vbs` のフルパスを指定。

### 手動
- `start.vbs` をダブルクリック（窓なしで起動）
- `start.bat` をダブルクリック（コンソール窓あり / デバッグ用）

## ツールの追加・編集

ランチャーUIから：
- **＋** ボタン → 名前 / パス / カテゴリ / 説明 を入力 → 保存
- 各行の **⋯** → 編集 or 削除

直接 `tools.json` を編集してもOK（保存すれば次回起動で反映）。

### スキーマ

```json
{
  "categories": {
    "core":     { "label": "Core",     "order": 1 },
    "coupon":   { "label": "Coupon",   "order": 2 },
    "analysis": { "label": "Analysis", "order": 3 },
    "chat":     { "label": "Chat",     "order": 4 },
    "utils":    { "label": "Utils",    "order": 5 },
    "misc":     { "label": "Misc",     "order": 9 }
  },
  "tools": [
    {
      "name": "Page Maker v12",
      "path": "/01_tools/core/page-maker-v12.html",
      "category": "core",
      "description": "短い説明（省略可）",
      "hidden": false
    }
  ]
}
```

`hidden: true` で一時非表示。`path` は外部URL（`https://...`）も可。

## 環境前提

- **Python 3.x** が PATH に通っていること（`pythonw -m http.server` 系の serve.py を実行）
- **Microsoft Edge** または **Google Chrome**（ポップアップ窓化のため。無くてもブラウザタブで動作はする）
- 自宅/職場ともに同じ git リポジトリをクローンしてあること
- ELECOM側設定はマシン毎 → 各マシンで一度 `start.vbs` のフルパスを指定

## 既存 start-server.bat との関係

リポジトリ直下の `start-server.bat`（port 8080 / Canvas🚀ボタン用）はそのまま。本ランチャーは port 8765 で独立動作。両方同時起動可。
