# 01_tools/launcher/

**自作ランチャー。ボタンで画面右端に縦長サイドバーがトグル表示 → ツール一覧 / 追加 / 編集 / 削除。**

## 構成

| ファイル | 役割 |
|----------|------|
| `start.vbs` | ELECOMボタン等から呼ぶ入口。コンソール窓を出さずに start.bat を起動 |
| `start.bat` | port 8765 で `serve.py` を確保 → `panel.ps1` に窓制御を委譲。引数 `server` でサーバのみ起動（窓を開かない）|
| `panel.ps1` | サイドバー窓の制御。Chrome/Edge `--app` を**右端ドック・縦フル・常に最前面**で起動し、開/閉を**トグル**（`-Action toggle\|open\|close`）|
| `serve.py` | カスタム HTTP サーバ。`GET/POST /api/tools`(tools.json読み書き) / `GET /api/browse`(ファイル選択ダイアログ) / `POST /api/launch`(ローカルアプリ起動)。静的配信はリポジトリルート起点 |
| `server.vbs` | スタートアップ用。窓を開かずサーバだけ常駐させる（`start.bat server` を窓なしで呼ぶ）|
| `index.html` | サイドバーUI（検索・カテゴリ別表示・行クリック起動・⋯から編集・＋から追加） |
| `tools.json` | ツール登録（永続データ） |

## 設計のポイント

### サイドバー挙動（panel.ps1）
- **画面右端ドック**: 作業領域（タスクバー除く）の右端に幅360px・縦フルで配置
- **常に最前面**: 起動後に窓HWNDを `SetWindowPos(HWND_TOPMOST)` でピン留め（user32 P/Invoke）
- **トグル開閉**: ボタンを押すと出る／もう一度押すとしまう。窓の有無は EnumWindows でタイトル `PFD Launcher` を検索して判定 → **多重起動（窓が増える）しない**
- 窓を閉じても**サーバは常駐**（軽いので次回が速い）。閉じるのは窓だけ
- Chrome 優先 → Edge → 既定ブラウザにフォールバック（フォールバック時のみドック不可）

### サーバ（serve.py / start.bat）
- 専用 user-data-dir（`%LOCALAPPDATA%\PFDLauncher\edge-profile`）で通常Edge/Chromeと**プロファイル分離**
- サーバルート = **リポジトリルート** → tools.json の path は `/01_tools/core/xxx.html` のような絶対パス
- `%~dp0` で自身位置から相対起動 → **自宅/職場でクローン先パスが違っても動く**
- 起動済み判定は `netstat` の LISTENING チェック（閉じたポートは即拒否されず約1〜2秒ハングするため、HTTPプローブだと毎回タイムアウト分を浪費する）。probe・URLは `127.0.0.1` 固定（`localhost` のIPv6遅延回避）
- バックグラウンドサーバは `pythonw` で起動 → 黒い窓は一切出ない

## 起動方法

### ELECOMトラックボール（推奨）
マウスアシスタント → 空きボタン → **「ファイルを指定して実行」** → `start.vbs` のフルパスを指定。
押すたびにサイドバーが**開閉トグル**する。

### スタートアップ常駐（任意・軽い）
`server.vbs` への**ショートカットをスタートアップフォルダ**（`shell:startup`）に置くと、PC起動時にサーバだけ常駐し、初回のボタン押下が一瞬で開く。
- サーバ常駐の負荷: idle pythonw ≈ RAM 10〜15MB / CPUほぼ0%（窓を開いていなければブラウザのメモリは消費しない）
- 解除: スタートアップフォルダの `PFD Launcher Server.lnk` を削除するだけ

### 手動
- `start.vbs` をダブルクリック（窓なしで起動／トグル）
- `start.bat` をダブルクリック（コンソール窓あり / デバッグ用）
- `start.bat server` … サーバのみ起動（窓を開かない）

## ツールの追加・編集

ランチャーUIから：
- **＋** ボタン → **種類〔Web / アプリ〕** を選択 → 名前 / パス / カテゴリ / 説明 → 保存
- 各行の **⋯** → 編集 or 削除

直接 `tools.json` を編集してもOK（保存すれば次回起動で反映）。

### 登録できる3種類

| 種類 | `type` | `path` の中身 | 開き方 | 📁ボタン |
|------|--------|--------------|--------|---------|
| HTMLツール | `web`(既定) | `/01_tools/core/xxx.html` | ブラウザ（リンク） | リポジトリ内HTML選択 |
| 外部URL/Webサービス | `web`(既定) | `https://...` | ブラウザ（リンク） | （手入力） |
| ローカルアプリ | `app` | `.exe` / `.lnk` の**絶対パス** | サーバが `os.startfile` で起動 | .exe/.lnk選択（スタートメニュー起点） |

**Chrome/Edgeで「アプリとしてインストール」したやつ(PWA)** は、スタートメニューに `.lnk` ショートカットが作られる → 種類「アプリ」の 📁 で選ぶだけで登録・起動できる（exe も PWA も同じ仕組み）。アプリ行には `APP` バッジが付く。

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
      "name": "Excel",
      "path": "C:\\Users\\xxx\\...\\Excel.lnk",
      "category": "utils",
      "type": "app"
    }
  ]
}
```

- `type` 省略時は `web`（ブラウザで開く）。`type: "app"` で**ローカル起動**（path は絶対パス）。
- `hidden: true` で一時非表示。`web` の `path` は外部URL（`https://...`）も可。
- `app` 起動はローカルでexeを実行するため、`serve.py` は **127.0.0.1限定 + 存在する絶対パスのファイルのみ**に制限してガードしている。

## 環境前提

- **Python 3.x** が PATH に通っていること（`pythonw -m http.server` 系の serve.py を実行）
- **Microsoft Edge** または **Google Chrome**（ポップアップ窓化のため。無くてもブラウザタブで動作はする）
- 自宅/職場ともに同じ git リポジトリをクローンしてあること
- ELECOM側設定はマシン毎 → 各マシンで一度 `start.vbs` のフルパスを指定

## 既存 start-server.bat との関係

リポジトリ直下の `start-server.bat`（port 8080 / Canvas🚀ボタン用）はそのまま。本ランチャーは port 8765 で独立動作。両方同時起動可。
