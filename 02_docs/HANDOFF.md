# HANDOFF.md — 現在地（Prop Firm Challengers / propfirm-database）

## 運用ルール
- **このファイルは「現在地」のみを保持する。常に上書き、追記しない。**
- 過去のセッションログ・旧仕様は [HANDOFF_archive.md](HANDOFF_archive.md) 参照。**通常は読まなくてよい**。
- 起動時必読順: `CLAUDE.md` → `PROJECT_MAP.md` → `HANDOFF.md`（本ファイル） → メモリ`MEMORY.md`

最終更新: 2026-06-14（セッション18・収集コックピット＋help-index 18社）

> 詳細な過去ログは [HANDOFF_archive.md](HANDOFF_archive.md) の「セッション17-18」参照。

---

## 現在地

**フェーズ: Firm Database 収集コックピット稼働 / help-index 横展開中**

```
収集: NotebookLM(主・公式URL保管) ＋ Web2MD(補完)
  → Page Maker取込 → data/firms/*.json + data/plans/*.json（公開層・1プラン1ファイル）
網羅: firm-database.html の 📡 で Firm網羅(F/22・slot_urls)＋Plan網羅(P/21・help-index) を可視化
```

### 直近の状態
- **Firm Database = 全作業の起点・管制塔**（`01_tools/core/firm-database.html`・FD-11〜17 収集コックピット）。データ源 localhost:8765 `agent.py`（要再起動で反映）
- **help-index 18社**（`_work/help-index/{slug}.json` 記事→P-スロット地図）: **平均18.6/21**（6社20-21、15社≥18）。fundingpips=本文確定`ok`、他は`auto+body`（記事本文を具体フレーズ照合・要レビュー）。生成=`scripts/harvest-help-index.py`、本文補強=`scripts/refine-help-index.py`。残低: finotive(16)・maven(10・inline_accordionで本文補強対象外)
- **FD-17 NotebookLM適性**: 🩺チェックで各URLを ✅投入可/⚠️JS描画=空ソース恐れ/❌ブロック に分類（閾値 NLM_TEXT_MIN=1200字）
- **fundingpips v2 完了**: `_work/firms-v2/fundingpips.md`（F01-F22の18項目＋比較表＋5プラン×21 P-スロット=195行）。`/normalize-firm-v2` スキル（GoogleDrive管理）
- **公開層 data/firms 34・data/plans 28 は worklist 保持**（中身はv1由来・信頼不可・v2で順次上書き）
- **継続資産**: `_work/firm-slot-urls.json`(32社URL↔スロット)、`_work/price-collect/wide/`(26社価格)、`data/glossary.json`(149)

### Web2MD MCP（セッション16導入）
- 設定: `.mcp.json` の `web2md` エントリ（APIキーenv直書き、`.gitignore`対象）
- 自宅PC拡張ID: `ijmgpkkfgpijifldbjafjiapehppcbcn`
- APIキー: `w2m_4a5f67f52f47823b08e8a988304bcfaeb8869bbcc30817f5ef378ccf89c815fa`（アカウント単位・全PC共通）
- ツール: `convert_url` / `agent_convert` / `bridge_convert_url` 等
- **実運用ルート**: マスターのChromeでURL開く → 拡張ポップアップ「Download」 → `data/scans/{slug}.md` 落とす（`_work/scans/{slug}.md`）→ ソートーが分割・正規化（サーバー側fetchはWAFで403、agent_convertはport12315起動条件あり）

### 別PC（職場等）でのWeb2MDセットアップ手順
`.mcp.json` は `.gitignore` 対象でPC毎に作成必要:
1. Chrome に Web2MD 拡張インストール（[web2md.org](https://web2md.org) ログイン → 拡張インストール、**拡張IDは別IDが割当**）
2. `npm install -g web2md-mcp-server`
3. `npx web2md-mcp-server-install <その PC の拡張ID>` で Native Messaging Host 登録
4. `.mcp.json` に web2md エントリ追加（上記APIキー使用）
5. Chrome 再起動 + Claude Code 再起動 → `/mcp` で `web2md ✓ connected` 確認

---

## 確定した設計判断（覆さない）

| # | 決定 | 補足 |
|---|---|---|
| 1 | 起動時必読順は `CLAUDE.md → PROJECT_MAP.md → HANDOFF.md → メモリ` | 構造=MAP、進捗=本ファイル、好み=メモリ |
| 2 | v2 収集は `Web2MD手動Download → split-web2md-dump → firms-v2/{slug}.md → Page Maker取込` | v1（scan+Playwright→.pipe.md）は廃止削除済 |
| 3 | ツールは `start-server.bat`（localhost:8080）経由。`file://` 不可（CORS） | |
| 4 | Page Maker (`01_tools/core/page-maker-v12.html`) の `MASTER_DEFS` がスロット定義の唯一の正本 | 直接編集禁止 |
| 5 | `_work/scans/` はGit管理対象外（**.gitignore追加・追跡解除 済 / セッション18bで解消**） | 旧パス `data/scans/` |
| 6 | AI用の仕組み整備はソートーが判断して実装。マスターへの方法確認は不要 | メモリ `feedback-autonomy` |
| 7 | Hugoは本環境でビルド不可（Application Control）。見た目最終確認はマスター側ターミナル | |
| 8 | v2 ファイル拡張子は `.md`（`.pipe.md` ではない）。v1と混同しない | |
| 9 | Web2MD APIキーは `.mcp.json` env に直書き。`.env` ではなくMCPサーバー設定として保持 | |
| 10 | **`firm-database.html`（Firm Dashboard）が全作業の起点・管制塔。閲覧系は今後ここに集約**。1社編集は page-maker を FD-08 から起動 | 旧 firm-dashboard/firm-urls/firm-tour は廃止吸収。データは localhost:8765 agent.py（/api/firms,/api/progress）。新機能は FEATURE_INDEX に FD-xx 追加 |
| 11 | **Firm=1ファイル / Plan=プランごと1ファイル の非対称は確定仕様**。編集ソース `firms-v2/{slug}.md` は全プラン内包（1社1file）、出力JSONは `firms/{slug}.json` 1本＋`plans/{firm}--{plan}.json` 複数に分解 | Hugoが「1プラン1ファイル」前提（plans/single.html=キー引き、list/firm/ranking=range）。比較表はプラン＝1行なのでデータもプラン単位が最も素直。Plan内包(b/c)は採らない |
| 12 | **`data/`=公開層（Hugoが読む正本のみ）/ `_work/`=作業層（Hugo対象外）**。Hugoは `data/` 全JSONを無条件ロードするため両層を物理分離 | `data/`に置くのは firms/ plans/ glossary.json coupon-config.json のみ。ドラフト/収集生/状態/レジストリは `_work/`。各層 `_README.md` 参照。パス正本は agent.py（FIRMS_EDIT_DIR/PROGRESS_FILE）と各script |

---

## 次にやること（要再確認・優先順）

0. **launcher: ツールが narrow 幅で開く / Alt+数字キー無反応 を解決中** — セッション16後半で agent.py に `/api/open-url`（Chrome を `--app=URL --window-size=W,H` で別プロセス起動）追加・index.html を agent経由に切替・wincontrol.py に foreground 強奪追加。**未動作確認のまま中断**。職場側で動作確認 → 修正継続。
1. **fundingpips Page Maker 取込テスト** — Firmタブ新規作成 → 貼付 → 「格納」 → 「▶Planタブ生成」 → 「全プラン」で v2 ワークフロー全体検証
2. **v2 横展開** — 候補: 価格未収集5社（the5ers, ment-funding, qt-funded, audacity-capital, hola-prime）または取得実績ある他社
3. **URL taker → firm-tour 直送連携の設計** — `_work/firm-slot-urls.json` のメンテ経路（firm-tour は廃止済みのため Firm Database 側への再設計が前提）
4. **定期巡回・差分検知システムの設計** — fundingpipsで404多発したように URL構造変更検知が必要
5. **Discord収集システム実装** — 設計: [`discord-collector_v1_proposal.md`](discord-collector_v1_proposal.md)
6. **`_work/price-collect/wide/` の v2 ファームファイルへの統合** — 26社分の横持ち価格表を再利用

---

## 留意点

- BLOCKEDファーム判定の訂正: 完全ブロックは **fundingpips のみ**。Web2MD Agent Bridge手動経路で突破可能と実証済
- `_work/firm-slot-urls.json` の URL は腐敗例あり（fundingpipsの `trading-rules/fp-evaluation/` `/faq` `payouts collection` は404）。定期巡回の主要動機の一つ
- `_work/firm-slot-urls.json` の `slot_urls`/`plan_urls` 件数は社により大きく異なる（3〜21件）。データ欠損ではなく実際のページ構成差
