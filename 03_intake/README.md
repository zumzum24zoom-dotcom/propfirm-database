# 03_intake — データ入力 作業フォルダ

ソートー（Claude）専用のデータ入力ワークスペース。**本番 `data/` を直接触らないための隔離領域**。

## ★基本方針：非破壊・追記優先

NotebookLM 出力 → Page Maker でほぼ充填され、**埋まらなかった項目をソートーが補完**する役割分担。
ソートーの書き込みは以下を厳守する：

| 状況 | 動作 |
|------|------|
| 空の項目 | 埋める |
| 既に値がある項目 | そのまま保持（触らない） |
| 既存項目への追加情報 | 別フラグメントとして追記（既存を消さない） |
| **上書き** | **「明示的な上書き指示」または「明らかな誤り」がある時のみ** |

## ファイル

| パス | 役割 |
|------|------|
| `03_intake/intake-sotoh.json` | **ソートー作業用**JSON。構造は `{ firms, tabDataMap, glossaryTerms }`。ソートーがここに追記 → マスターがチェック |
| `data/pfdb.json` | **マスター正本**。マスターが Page Maker から保存・維持する本番データ |
| `screenshots/` | チャットに貼る前後のスクショ置き場（任意保管） |

## データの流れ（責任分界）

```
ソートー → 03_intake/intake-sotoh.json へ追記
            ↓（マスターが Page Maker で「読込」してチェック）
       Page Maker 画面で確認・微修正
            ↓（マスターが「🚀 Hugo / 全保存」）
       data/pfdb.json ・ 本番 data/ ・ content/ へ反映
                                  ← ここは Page Maker / マスターだけが書く
```

- **ソートーは `03_intake/` だけに書く**
- **本番 `data/` ・ `content/` は Page Maker だけが書く**

## ルール

1. ソートーが書き込む前に、**抽出値を必ずチャットへ提示しマスターの承認を取る**（トレードルールの数値ミス防止）
2. Page Maker の「読込」は**現在のデータを丸ごと置き換える**ため、この作業ファイルは常に「既存全ファーム＋新規」を保持する（空から作らない）
3. 新規 Firm/Plan の id は既存最大値+1 で採番し、衝突させない
4. ソートーがJSONを書いている最中、マスターは Page Maker 側で「保存」しない（衝突防止）。手順は「ソートーが書く → マスターが読込」の一方向

## 入力ワークフロー（スクショ起点）

1. Obsidian で Firm の HP を開く
2. スクショを撮る（概要／料金表／ルール詳細／出金 など断面ごとに複数枚推奨）
3. チャットに貼る
4. ソートーが解析 → 抽出値を提示 → 承認後に `intake-sotoh.json` へ追記
5. マスターが Page Maker で「読込」→ 確認 →「🚀 Hugo / 全保存」で `data/pfdb.json`・本番反映

## スロット定義（参照）

- **DBP_01 Firm（22）**: firmName, country, established, officialUrl, firmCategory, japanChat, firmPitch, rewardProgram, scaleUp, broker, platform, serverTime, ddReset, leverage, commission, paymentMethods, payoutMethods, payoutPolicy, profitSplit, profitSplitNote, planComparison, planList
- **DBP_02 Plan（22）**: challengeName, priceTable, ruleQuickRef, rd_target, rd_minDays, rd_dailyLoss(+Type), rd_maxLoss(+Type), rd_consistency, rd_profitCap, rd_timeLimit, rd_news, rd_weekend, rd_overnight, rd_ea, rd_copyTrade, rd_scalping, rd_stopLoss, rd_risk, rd_maxPosition, rd_prohibited
