# 01_tools/launcher/

**自作ランチャー兼サイドバー。常駐エージェント(agent.py)がサーバー・クリップボード履歴・グローバルホットキーをまとめて担当。**

## 構成

| ファイル | 役割 |
|----------|------|
| `agent.py` | **常駐プロセス**。port 8765 のHTTPサーバー（tools.json読み書き・ファイル選択・アプリ起動・クリップボード履歴API）+ Win32メッセージループ（クリップボード監視・グローバルホットキー・ウィンドウ制御） |
| `register-startup.ps1` | `agent.py` をWindowsログオン時に自動起動するタスクスケジューラ登録スクリプト（初回1回実行） |
| `clipboard_store.py` | クリップボード履歴のSQLite保存・画像PNG保存（`clipboard_data/`、Git管理外） |
| `wincontrol.py` | クリップボード読み書き・サイドバー窓のshow/hide・最前面切替のWin32ラッパー |
| `start.vbs` | ELECOMボタン等から呼ぶ入口。コンソール窓を出さずに start.bat を起動 |
| `start.bat` | エージェントに `/api/window/toggle` を投げてサイドバーの表示/非表示を切替。エージェント未起動なら起動してからリトライ |
| `index.html` | ポップアップUI。Tools / Clipboard タブ、検索・カテゴリ別表示・行クリック起動・⋯から編集・＋から追加・📌で最前面固定 |
| `tools.json` | ツール登録（永続データ） |
| `requirements.txt` | `pip install -r requirements.txt`（pywin32, Pillow） |

## 初回セットアップ

1. `pip install -r requirements.txt`
2. `register-startup.ps1` を右クリック→PowerShellで実行（タスク登録 + 即起動）
3. 以後はWindowsログオン時に `agent.py` が自動起動

タスク解除: `Unregister-ScheduledTask -TaskName "PFDLauncherAgent" -Confirm:$false`

## 設計のポイント

- **常駐エージェント方式**: `agent.py` がログオン時から常駐するため、開閉のたびにサーバー起動・ポートチェック・PowerShell呼び出しを行わない（起動が遅い問題への対策）
- **グローバルホットキー Insert**: どこからでもサイドバー窓の表示/非表示をトグル（未起動なら新規起動）
- **📌最前面固定**: UIのピンボタンから `/api/window/topmost` を呼び、サイドバー窓のTOPMOSTを切替
- **Edge `--app` モード** で開くのでタブ・URLバーなしの**独立ポップアップ窓**（幅360px・画面右端にドッキング・専用プロファイルで通常Edgeと分離）。開閉時は右端へのスライドイン/アウト演出
- **クリップボード履歴（テキスト＋画像）**: `AddClipboardFormatListener`で監視 → SQLite + PNGファイルに保存（最大200件、超過分は自動削除）。Clipboardタブから一覧・コピー復元・削除・全削除
- **数字キー1〜9 クイック起動**: 表示中のツール先頭9件に番号バッジが付き、数字キーで即起動（検索欄をクリックして入力中は数字キーを通常入力として扱う。Alt+数字はOSの隠しメニューに奪われるため不採用）
- 多重起動防止: `/api/ping` で既存エージェントを検知

## ツールの追加・編集

ランチャーUIから：
- **＋** ボタン → 種別 / 名前 / パス / カテゴリ / 説明 を入力 → 保存
- 各行の **⋯** → 編集 or 削除

直接 `tools.json` を編集してもOK（保存すれば次回起動で反映）。

### 種別 (`type`)

| type | 用途 | `path` の内容 | 起動方法 |
|---|---|---|---|
| `html`（省略可・既定） | HTMLツール / Webページ | `/01_tools/core/xxx.html` または `https://...` | `<a target=_blank>` |
| `exe` | デスクトップアプリ・ファイル | ローカル絶対パス（例: `C:\Apps\foo.exe`） | `/api/launch` → `os.startfile` |
| `pwa` | インストール済みPWA/ストアアプリ | AppUserModelID（UI上は「アプリ選択」プルダウンから選択、`Get-StartApps`で取得） | `/api/launch` → `shell:AppsFolder\<AppID>` |

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
    },
    {
      "name": "NotebookLM",
      "path": "Google.NotebookLM_xxxxx!App",
      "type": "pwa",
      "category": "chat"
    }
  ]
}
```

`hidden: true` で一時非表示。

## 環境前提

- **Python 3.x** が PATH に通っていること（`pythonw agent.py` を実行）
- **pywin32 / Pillow**（`requirements.txt`）
- **Microsoft Edge** または **Google Chrome**（ポップアップ窓化のため。無くてもブラウザタブで動作はする）
- 自宅/職場ともに同じ git リポジトリをクローンしてあること
- ELECOM側設定はマシン毎 → 各マシンで一度 `start.vbs` のフルパスを指定 + `register-startup.ps1` を実行

## 既存 start-server.bat との関係

リポジトリ直下の `start-server.bat`（port 8080 / Canvas🚀ボタン用）はそのまま。本ランチャーは port 8765 で独立動作。両方同時起動可。
