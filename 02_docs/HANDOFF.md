# HANDOFF.md — 現在地（Prop Firm Challengers / propfirm-database）

## 運用ルール
- **このファイルは「現在地」のみを保持する。常に上書き、追記しない。**
- 過去のセッションログ・旧仕様は [HANDOFF_archive.md](HANDOFF_archive.md) 参照。**通常は読まなくてよい**。
- 起動時必読順: `CLAUDE.md` → `PROJECT_MAP.md` → `HANDOFF.md`（本ファイル） → メモリ`MEMORY.md`

最終更新: 2026-06-13（セッション16）

---

## 現在地

**フェーズ: v1廃止完了・v2（Web2MD経由）パイプライン稼働開始**

```
Web2MD Chrome拡張（人間ブラウザで取得）
  → data/scans/{slug}/*.md（記事単位）
  → scripts/split-web2md-dump.mjs（連続ダンプ分割）
  → 手動正規化 → data/firms-v2/{slug}.md
  → Page Maker取込 → data/firms/*.json + data/plans/*.json（自動上書き）
```

### 直近の状態
- **fundingpips v2 完了**: 13記事取得、`data/firms-v2/fundingpips.md` 生成（F01-F22中18項目埋め＋5プラン比較表＋全価格セル充填）
- **v1廃止削除済**: 107ファイル + 2スキル削除（詳細はarchive）
- **保護残置**: `data/firms/*.json` 34本 / `data/plans/*.json` 28本（v2取込で順次上書きされる設計のため。中身はv1由来で全て信頼不可）
- **継続使用資産**: `data/firm-slot-urls.json`（URLレジストリ）、`data/price-collect/wide/`（26社価格表横持ち）、`data/glossary.json`

### Web2MD MCP（セッション16導入）
- 設定: `.mcp.json` の `web2md` エントリ（APIキーenv直書き、`.gitignore`対象）
- 拡張ID: `ijmgpkkfgpijifldbjafjiapehppcbcn`
- ツール: `convert_url` / `agent_convert` / `bridge_convert_url` 等
- **実運用ルート**: マスターのChromeでURL開く → 拡張ポップアップ「Download」 → `data/scans/{slug}.md` 落とす → ソートーが分割・正規化（サーバー側fetchはWAFで403、agent_convertはport12315起動条件あり）

---

## 確定した設計判断（覆さない）

| # | 決定 | 補足 |
|---|---|---|
| 1 | 起動時必読順は `CLAUDE.md → PROJECT_MAP.md → HANDOFF.md → メモリ` | 構造=MAP、進捗=本ファイル、好み=メモリ |
| 2 | v2 収集は `Web2MD手動Download → split-web2md-dump → firms-v2/{slug}.md → Page Maker取込` | v1（scan+Playwright→.pipe.md）は廃止削除済 |
| 3 | ツールは `start-server.bat`（localhost:8080）経由。`file://` 不可（CORS） | |
| 4 | Page Maker (`01_tools/core/page-maker-v12.html`) の `MASTER_DEFS` がスロット定義の唯一の正本 | 直接編集禁止 |
| 5 | `data/scans/` はGit管理対象外（**.gitignore追加は未実施**） | |
| 6 | AI用の仕組み整備はソートーが判断して実装。マスターへの方法確認は不要 | メモリ `feedback-autonomy` |
| 7 | Hugoは本環境でビルド不可（Application Control）。見た目最終確認はマスター側ターミナル | |
| 8 | v2 ファイル拡張子は `.md`（`.pipe.md` ではない）。v1と混同しない | |
| 9 | Web2MD APIキーは `.mcp.json` env に直書き。`.env` ではなくMCPサーバー設定として保持 | |

---

## 次にやること（要再確認・優先順）

1. **fundingpips Page Maker 取込テスト** — Firmタブ新規作成 → 貼付 → 「格納」 → 「▶Planタブ生成」 → 「全プラン」で v2 ワークフロー全体検証
2. **v2 横展開** — 候補: 価格未収集5社（the5ers, ment-funding, qt-funded, audacity-capital, hola-prime）または取得実績ある他社
3. **`data/scans/` の `.gitignore` 追加** — 決定済み・未実施
4. **launcher 系の未コミット変更整理**（`agent.py` 等の untracked / `_README.md` `index.html` `start.bat` の M）— セッション16では別マシン側の launcher 履歴が16コミット先行していたため、本セッションの launcher 変更は別途master判断
5. **URL taker → firm-tour 直送連携の設計** — `data/firm-slot-urls.json` のメンテ経路
6. **定期巡回・差分検知システムの設計** — fundingpipsで404多発したように URL構造変更検知が必要
7. **Discord収集システム実装** — 設計: [`discord-collector_v1_proposal.md`](discord-collector_v1_proposal.md)
8. **`data/price-collect/wide/` の v2 ファームファイルへの統合** — 26社分の横持ち価格表を再利用

---

## 留意点

- BLOCKEDファーム判定の訂正: 完全ブロックは **fundingpips のみ**。Web2MD Agent Bridge手動経路で突破可能と実証済
- `data/firm-slot-urls.json` の URL は腐敗例あり（fundingpipsの `trading-rules/fp-evaluation/` `/faq` `payouts collection` は404）。定期巡回の主要動機の一つ
- `data/firm-slot-urls.json` の `slot_urls`/`plan_urls` 件数は社により大きく異なる（3〜21件）。データ欠損ではなく実際のページ構成差
