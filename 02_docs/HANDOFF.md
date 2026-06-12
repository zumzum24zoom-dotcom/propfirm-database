# HANDOFF.md — 現在地（Prop Firm Challengers / propfirm-database）

## 運用ルール
- **このファイルは「現在地」のみを保持する。常に上書き、追記しない。**
- 過去のセッションログ・旧仕様（Page Maker v11/Widget Maker期）は [HANDOFF_archive.md](HANDOFF_archive.md) 参照。**通常は読まなくてよい**。
- セッション終了時: 「現在地」「確定した設計判断」「次にやること」を最新化。詳細な作業ログを残したい場合のみ archive 末尾に追記。
- 起動時必読順: `CLAUDE.md` → `PROJECT_MAP.md` → `HANDOFF.md`（本ファイル） → メモリ`MEMORY.md`

最終更新: 2026-06-12（セッション15）

---

## 現在地

**フェーズ: データ収集パイプライン稼働中 ＋ ランチャー整備完了**

```
data/scans/ + data/help-index/ → /normalize-firm → data/firms/{slug}.pipe.md
   → Page Maker取込 → exportHugo → master承認 → data/firms/*.json + data/plans/*.json
```

- help-index: 32/33社完了（fundingpips=blocked要手動、atfunded=対象外）
- normalize-firm: 30社の `.pipe.md` 生成済み。**Page Maker取込・exportHugo はまだ未実施**
- `data/firm-slot-urls.json`: 32社分の slot_urls/plan_urls 完成済み
- `01_tools/core/firm-tour.html`: 上記JSONを表示するビューア。今セッションで `SLOT_URL` 参照を修正（`../../data/firm-slot-urls.json` 相対パス化）し、32/32社の表示を確認済み

### ランチャー（セッション15で整備完了・push済み）
- `panel.ps1` 新規追加 — 右端ドックサイドバー・常に最前面・トグル開閉
- `server.vbs` 新規追加 — スタートアップ常駐用
- `serve.py` 更新 — `/api/launch`（アプリ起動）・ブラウズ種別分岐（html/app）追加
- `index.html` 更新 — APP種別・バッジ・セグメントトグル追加
- `tools.json` 更新 — firm-urls・NotebookLM 追加
- **未コミット**: AutoHotKey ホットキースクリプト（自宅のみ存在。次回帰宅時にコミット要）

**進行中の構想（master発案）**: URL自動取得 → 直送保存 → 再利用 → ページ内容をPage Makerスロットにマッピング保存 → 定期巡回 → 差分検知。
- 既存パーツ: `01_tools/utils/BLT/URL taker`（収集ブックマークレット）/ `firm-tour.html`（閲覧ビューア）/ `data/firm-slot-urls.json`（URLレジストリ候補）
- 未実装: URL taker → firm-tour 直送連携、定期巡回、差分検知ロジック

---

## 確定した設計判断（覆さない）

| # | 決定 | 補足 |
|---|---|---|
| 1 | 起動時必読順は `CLAUDE.md → PROJECT_MAP.md → HANDOFF.md → メモリ` | 構造=PROJECT_MAP.md、進捗=HANDOFF.md、好み=メモリ で重複させない |
| 2 | データ収集は `scans/help-index → normalize-firm → firms/plans draft → master承認` の一本道 | ライブフェッチではなく既存スキャンデータから正規化 |
| 3 | ツールは `start-server.bat`（localhost:8080）経由で開く。`file://` 不可（CORS） | `firm-tour.html` 等のfetch()がCORSで失敗するため |
| 4 | Page Maker (`01_tools/core/page-maker-v12.html`) の `MASTER_DEFS` がスロット定義の唯一の正本 | SLOT_DEFS/GLOSSARY_SEED等はここから自動導出、直接編集禁止 |
| 5 | `data/scans/` はGit管理対象外（ローカルのみ） | 将来の差分検知ベースライン用に残すが、容量・ノイズの理由でリポジトリには含めない（**.gitignore追加は未実施**） |
| 6 | AI用の仕組み整備（フォルダ構成・README・スキーマ・本ファイルの構造など）はソートーが判断して実装。マスターへの方法確認は不要 | メモリ `feedback-autonomy` |
| 7 | Hugoは本環境でビルド不可（Application Control）。見た目最終確認はマスター側ターミナル | hugo-devスキル等で対応 |

---

## 次にやること（要再確認・優先順）

0. **AutoHotKey ホットキースクリプトのコミット** — 自宅帰宅時に `01_tools/launcher/hotkey.ahk` を git add してプッシュ
1. **`data/scans/` の `.gitignore` 追加** — 決定済み・未実施
2. **未コミット変更の整理**（`firm-tour.html`修正、`01_tools/utils/`再編、URL taker追加、price-scanner.js追加など） — コミットタイミングを master に確認
3. **firm-tour.html の仕事場動作確認** — `start-server.bat`経由か`file://`か未確認。`file://`の場合は要対策
4. **URL taker → firm-tour 直送連携の設計** — 収集したURLを `{url,label,slots}` 形式にラベリングし `data/firm-slot-urls.json` にマージする経路
5. **normalize-firm draft → Page Maker取込 → exportHugo**（セッション11から持ち越し） — 30社の `.pipe.md` をPage Makerに取り込み、`data/firms/*.json` / `data/plans/*.json` を再生成
6. **fundingpips 手動確認** — bot対策のためブラウザ手動操作でhelp-index/normalize-firm実施
7. **定期巡回・差分検知システムの設計** — `data/firm-slot-urls.json` をURLレジストリとして利用する構想
8. **Discord収集システム実装** — 設計: [`discord-collector_v1_proposal.md`](discord-collector_v1_proposal.md)（クーポン・出金情報を32ファームのDiscord公式チャンネルから定期収集）

---

## 留意点

- BLOCKEDファーム5社（fundingpips, e8-markets, moneta-funded, atmos-funded, funded-trading-plus）はbot対策で自動操作不可。`firm-tour.html`では「⚠手動」表示。
- `data/firm-slot-urls.json` の `slot_urls`/`plan_urls` 件数は社により大きく異なる（3〜21件）。データ欠損ではなく実際のページ構成差。
