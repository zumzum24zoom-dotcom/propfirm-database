# _work/firms-edit/

**page-maker改「1社モード」の編集ドラフト置き場（`{slug}.json` = 1社1ファイル）。**

- Firm Database (`firm-database.html`) の「✏️編集」(FD-08) → page-maker `?firm={slug}` で起動し、この配下を読み書きする。
- 読み書きは agent.py の `/api/firm-edit` 経由（パス正本は `agent.py` の `FIRMS_EDIT_DIR`）。
- 公開層 `data/firms/{slug}.json` とは別。ここはあくまで作業ドラフト。

## 履歴

- 2026-06-14: v1由来の旧ドラフト33本を削除（中身は信頼不可・`pfdb.json`もろとも廃棄）。今後は実編集で1社ずつ再生成される。空フォルダ維持のため本READMEを置く。
