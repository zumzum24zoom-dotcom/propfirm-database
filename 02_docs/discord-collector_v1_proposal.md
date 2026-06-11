# Discord Collector v1 — 設計書（構想）

> **ステータス: 構想 / 未実装。**
> 実装着手＆設計承認時にファイル名から `_proposal` を外す。

最終更新: 2026-06-11（セッション14）

---

## 1. 背景・目的

掲載ファーム32社のうち多くが公式Discordサーバーを運用しており、以下の情報が**公式チャンネルに定型で投稿**されている：

- **クーポンコード**（プロモーション告知）
- **出金実績**（payout通知 / "user X got $Y"形式）
- **公式アナウンス**（規約変更・キャンペーン）
- **ユーザーの自由記述**（評判・トラブル報告など。雑談チャンネル）

これらを定期収集し、サイト（Hugo）に反映することで**鮮度の高い情報**を提供する。

---

## 2. スコープ確認（マスター判断済）

| 項目 | 決定 |
|---|---|
| **収集対象** | クーポン + 出金情報（公式 / ユーザー双方） |
| **対象サーバー数** | 32（=掲載ファーム数） |
| **マスター権限** | 一般メンバー（Bot招待権限なし） |
| **収集方式** | DiscordChatExporter (DCE) によるエクスポート方式 |

「公式チャンネル限定で構造化保存」 + 「雑談含めて生ログ保存」の**両方**を取る方針。

---

## 3. 全体構成

```
[Windows タスクスケジューラ 1日1回]
   ↓
[DCE CLI で増分エクスポート]
   ↓ JSON
[parser: 公式/ユーザー分類]
   ↓
   ├ data/coupons-discord.json     ← 公式クーポン（構造化）
   ├ data/payouts-discord.json     ← 公式payout（構造化）
   └ data/discord-rawlog/{server}/{channel}/{date}.json   ← 生ログ（雑談含む全部）
   ↓
[Hugo build] → サイト反映（クーポン・出金実績ページ）
```

---

## 4. データ構造

### 4.1 channel registry `data/discord-channels.json`

```json
{
  "servers": [
    {
      "firm_slug": "ftmo",
      "server_id": "123456789012345678",
      "server_name": "FTMO Official",
      "channels": [
        { "id": "111", "name": "announcements", "type": "official", "purpose": "アナウンス" },
        { "id": "222", "name": "payouts",       "type": "official", "purpose": "出金通知" },
        { "id": "333", "name": "promotions",    "type": "official", "purpose": "クーポン" },
        { "id": "444", "name": "general",       "type": "user",     "purpose": "雑談" }
      ],
      "last_fetched_at": "2026-06-11T00:00:00Z"
    }
  ]
}
```

- `type: "official"` → parser で構造化抽出（regex/Bot投稿パターン）
- `type: "user"` → 生ログ保存のみ（後段でLLM分類オプション）

### 4.2 `data/coupons-discord.json`

```json
{
  "updated_at": "2026-06-11T00:00:00Z",
  "coupons": [
    {
      "firm_slug": "ftmo",
      "code": "SUMMER25",
      "discount": "25%",
      "expires_at": "2026-07-01",
      "source_channel": "promotions",
      "source_message_id": "987654321",
      "source_url": "https://discord.com/channels/.../...",
      "captured_at": "2026-06-11T00:00:00Z",
      "raw_text": "..."
    }
  ]
}
```

### 4.3 `data/payouts-discord.json`

```json
{
  "updated_at": "2026-06-11T00:00:00Z",
  "payouts": [
    {
      "firm_slug": "ftmo",
      "amount_usd": 5000,
      "user_handle": "trader_x",
      "paid_at": "2026-06-10",
      "source_channel": "payouts",
      "source_message_id": "987654321",
      "captured_at": "2026-06-11T00:00:00Z"
    }
  ]
}
```

---

## 5. 段階的実装計画

| Phase | 内容 | 工数 | 完了条件 |
|---|---|---|---|
| **P1** | DCE導入 + channel registry作成 + 増分エクスポート + 生ログDB化 | 半日 | 32サーバー分の生ログJSONが `data/discord-rawlog/` に保存される |
| **P2** | クーポンコード抽出 (regex) → `coupons-discord.json` | 1-2h | 既知クーポンが取れる |
| **P3** | 出金情報抽出 (Bot投稿パターン認識) → `payouts-discord.json` | 1-2h | 公式Botのpayout通知が構造化される |
| **P4** | 出金情報の精度向上（LLM分類で雑談からも拾う / オプション） | 2-3h | ユーザー投稿の出金談から拾えるようになる |
| **P5** | Windowsタスクスケジューラ + Hugo統合 | 1h | 完全自動化（PC起動中） |

**P1だけで「毎日生ログが溜まる」状態**になる。抽出ロジックは後追いで足せる。

---

## 6. 抽出ロジック（参考）

### クーポンコード (P2)

```regex
\b([A-Z][A-Z0-9]{3,14})\b(?=.*?(code|promo|discount|off|%|クーポン|割引))
```

- 大文字英数字 4-15文字
- 周辺キーワード必須
- 割引率は `\d{1,2}%` で別途抽出
- 期限は日付パターン or `expires?`/`until`/`まで` 後の日付

### 出金情報 (P3)

公式Botは定型なのでファーム毎に1パターン用意：
- FTMO: `🎉 Congratulations <@user> received $\d+`
- Funded Next: 別パターン
- etc.

ファーム毎の正規表現を `data/discord-channels.json` の channel に持たせるか、別ファイル `data/discord-patterns.json` で管理。

### ユーザー投稿分類 (P4・オプション)

Claude API で「このメッセージは payout success / payout problem / その他」を分類。
- 1メッセージあたり数百トークン
- 32サーバー × 100msg/日 × 30日 = 月96000msg
- Sonnet なら月数百円〜千円程度

---

## 7. リスク・前提

| 項目 | 内容 | 対応 |
|---|---|---|
| **Discord ToS** | DCE は user token 使用。読み取り専用エクスポートだが規約上グレー | リスク許容。読み取り限定。投稿・自動操作はしない |
| **トークン漏洩** | user token = アカウント乗っ取りリスク | `.env` で管理、`.gitignore` 必須、コミット禁止 |
| **チャンネルID取得** | 開発者モードONで右クリック→IDコピー | 初回手動収集（マスター作業） |
| **PC稼働必須** | スケジューラ実行のためPC起動中である必要 | 将来GitHub Actionsへ移行（要トークン管理強化） |
| **画像クーポン** | スクショ投稿は取れない | OCR は範囲外。手動運用 |
| **メッセージ削除** | 削除されたメッセージは再エクスポートで消える | 生ログを `_rawlog/{date}.json` で日付スナップショット保存 |

---

## 8. 未決事項（マスター判断待ち）

- [ ] 32ファームのDiscordサーバーURL/招待リンク一覧（マスターが参加してるサーバーを集約）
- [ ] サーバーID・チャンネルIDの初回収集（マスターが手動取得）
- [ ] LLM分類を入れるか（P4 のスコープ判断）
- [ ] スケジューラ実行時刻（毎日 何時?）
- [ ] サイト表示への反映方法（クーポンページ・出金ランキング等の既存テンプレ拡張 or 新規）

---

## 9. 必要ツール・依存

- **DiscordChatExporter** (Tyrrrz/DiscordChatExporter): https://github.com/Tyrrrz/DiscordChatExporter
- Python 3.x（既存環境）
- （オプション）Claude API キー（P4 用）

---

## 10. 参考・関連

- `data/firm-slot-urls.json` — ファームURLレジストリ（Discord招待URLも追加できる）
- `01_tools/coupon/` — 既存のクーポン関連ツール（DOMスクレイパー）。本仕組みと並走
- `02_docs/HANDOFF.md` — 「次にやること」に本ファイルへの参照あり

---

## 11. 状態遷移

```
[現在] 構想 → discord-collector_v1_proposal.md
   ↓ マスター承認 + P1着手
[次] 実装中 → discord-collector_v1.md（_proposal外す）
   ↓ 大改訂
[未来] discord-collector_v2.md
```
