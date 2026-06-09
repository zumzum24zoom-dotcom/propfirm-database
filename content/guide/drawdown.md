---
title: "Drawdown（ドローダウン）完全解説"
category: "取引ルール"
tags: ["DD", "基礎"]
status: "done"
notion_id: "31c660a529e280f6bb62d799bdc96e98"
lastmod: 2026-05-03
---

Prop Firmにおける「Drawdown（ドローダウン）」とは、口座残高がピークからどれだけ減少したかを測る指標です。チャレンジ中もFunded後も、この制限を超えると即失格（Breach）になります。

Prop Firmのチャレンジでは、利益目標（Profit Target）を達成することよりも、このDrawdown制限を守り切ることの方が難しい場合が多いです。特にTrailing型のDrawdownは、計算方式を正確に理解していないと「なぜ失格したのかわからない」という事態になります。

Drawdownには **Daily Drawdown**（日次）と **Max Drawdown**（最大）の2種類があり、それぞれに計算基準（Type）が設定されます。

---

## Drawdownの2軸

|  | Daily Drawdown | Max Drawdown |
|---|---|---|
| **対象期間** | 1日（リセット時刻は各社のサーバー時間で定義） | 口座開設から全期間 |
| **計算** | 当日の最高値 - 現在値 | 全期間の最高値 - 現在値 |
| **典型的な上限** | 3%〜5% | 5%〜12% |

---

## Drawdown Typeの分類

DrawdownはStatic（固定型）か、Trailing（追従型）かで大きく2つに分かれます。

### Static（固定型）

初期残高を基準にした固定値です。口座開設時にBreach水準が決まり、その後は一切動きません。

> 例: 初期$100,000、Max DD 8% → Breach水準は常に$92,000

トレーダーにとって最も有利な方式です。利益が積み上がるほどBreach水準との差が広がり、実質的な余裕が増えます。

### Trailing（追従型）

残高が増えると、Breach水準も追従して引き上がります。Staticと違い、利益を出してもBreach水準との差はDD%のまま広がりません。

> 例: 初期$100,000、Max DD 8%。残高が$110,000に上がると、Breach水準も$102,000に上がる。利益$10,000出しても、Breachまでの余裕は常に$8,000。

---

## Drawdownの種類（6パターン体系）

Trailing型のDDは「High Water Mark（HWM / 最高到達値）」を追跡し、現在値がHWMからDD%以上下落するとBreachになります。Typeの違いは**3つの軸**の組み合わせで決まります。

1. **計算対象** — Balance（確定損益のみ）/ Equity（含み損益込み）/ Higher B or E（高い方）
2. **基準時** — EOD（取引日終了時のスナップショット）/ HWM（最高値更新時）

| # | Type | 計算対象 | 基準時 | HWM更新タイミング | 厳しさ |
|---|---|---|---|---|---|
| 1 | **Static** | — | — | 更新なし（初期残高で固定） | 最も緩い |
| 2 | **Trailing（Balance EOD）** | Balance | EOD | EOD時の確定残高でHWM更新 | 緩い |
| 3 | **Trailing（Balance HWM）** | Balance | HWM（決済時の残高） | 確定残高の最高値を追跡 | 厳しい |
| 4 | **Trailing（Equity EOD）** | Equity | EOD | EOD時のEquityでHWM更新 | やや緩い |
| 5 | **Trailing（Equity HWM）** | Equity | HWM（リアルタイム） | Equityの最高値をリアルタイム追跡 | 最も厳しい |
| 6 | **Trailing（Higher B or E EOD）** | Higher B or E | EOD | EOD時のB/Eの高い方でHWM更新 | 普通 |

### EODスナップショット方式（Type 2, 4, 6）

EOD（取引日終了時、通常NY 17:00）にスナップショットを取り、その値でHWMを更新します。日中の変動はHWMに反映されません。

- **Balance EOD** — 確定損益のみ。含み益が反映されない。最も緩やか
- **Equity EOD** — EOD時点の含み益が反映される
- **Higher B or E EOD** — BalanceとEquityの不利な方で判定。多くのファームの標準

> 例（Higher B or E EOD）: 日中にEquityが$115,000まで上昇。その後EOD時点でBalance $110,000 / Equity $108,000。HWMは$110,000（Balanceの方が高い）。日中の$115,000は無視される。

### HWM（最高値追従）方式（Type 3, 5）

EODスナップショットを持たず、対象値を最高値の更新の度に追跡し続けます。

- **Balance HWM** — 確定残高の最高値をリアルタイムで追跡
- **Equity HWM**（= Interday）— Equity（有効証拠金）をリアルタイムで追跡。ティックごとにHWMを更新し、日中のピークも全て拾う

> 例（Equity HWM）: 日中にEquityが$115,000に到達 → HWM = $115,000。その後含み益が縮小してEOD時点で$110,000でも、HWMは$115,000のまま。EOD型なら$110,000が基準になるが、Equity HWMでは$115,000が基準。

この特性から、Equity HWM型では「含み益を伸ばしてから利確する」という戦略が裏目に出ます。

---

## Daily DrawdownとType

Daily DDの基準値も、Max DDと同じ6パターン体系のType分類に従います。

- **EOD型**: 前日EODのスナップショット値が当日の基準。日中に利益が出ても基準は動かない
- **HWM型**: 日中の最高到達点が基準。含み益のピーク（Equity HWM）または確定残高の最高値（Balance HWM）を拾う

---

## Trailingはどこまで追従するか

- **Daily DD**: 失格（Breach）するまで追従が続く。ロックなし
- **Max DD**: 開始残高まで。Breach水準が開始残高に到達した時点でTrailingが停止し、以後Staticと同じ挙動になる

---

## 難易度の序列（トレーダー視点）

厳しい順に並べると：

1. **Trailing（Equity HWM）** — リアルタイムEquity追従。日中のピークを全て拾う。逃げ場なし（= Interdayともいう）
2. **Trailing（Balance HWM）** — 確定残高のリアルタイム追跡
3. **Trailing（Higher B or E EOD）** — EODスナップショット。BとEの不利な方で判定
4. **Trailing（Equity EOD）** — EODスナップショット。含み損益も反映
5. **Trailing（Balance EOD）** — EODスナップショット。確定損益のみ
6. **Static** — 固定値。利益が出るほど余裕が広がる

ファーム選びの際は、DD%だけでなくTypeも確認してください。同じ「Max DD 8%」でも、StaticとEquity HWMでは実質的な厳しさがまったく違います。

---

## まとめ

DrawdownはDD%だけでなく、Typeまで見て初めてそのプランの難易度がわかります。Staticなら利益が出るほど楽になり、Equity HWM（Interday）なら利益が出ても気が抜けない。
