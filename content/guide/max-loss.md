---
title: "Max Loss / Max Loss Limit / Max Drawdown の違いを解説"
category: "取引ルール"
tags: ["DD", "基礎"]
status: "draft"
notion_id: "2b3660a529e2803da9cfe2641138c619"
lastmod: 2026-03-09
---

このページでは、Prop Firm の評価・運用で頻出する **Max Loss / Max Loss Limit / Max Drawdown** の違いを整理します。

---

## 1. 用語のまとめ（ざっくり比較）

| 項目 | 日本語イメージ | 主な役割 |
|---|---|---|
| Max Loss | 最大損失額 | このチャレンジ／口座全体で「最終的にここまで損したらアウト」という累計損失ライン |
| Max Loss Limit | 最大損失限度額 | 上とほぼ同じ概念だが、「ルールとしての上限ライン」であることを強調した表現 |
| Max Drawdown | 最大ドローダウン（最大下落幅） | 口座のピーク（最高値）からどこまで下落してよいかを制限するルール。Static / Trailing などで挙動が変わる |

---

## 2. Max Loss（最大損失額）のイメージ

### 基本イメージ

- **初期口座金額の「何％まで負けてよいか」** を決めるルール
- 典型例：
  - 初期口座：**$100,000**
  - Max Loss：**10%**
  → **$10,000** までの損失は許容、それ以上は失格

### ポイント

- Static 型では **「初期口座金額 × パーセンテージ」で固定**（利益が出ても Max Loss は動かない）
- Challengeを選ぶ時は **Static 型か Trailing 型か** を必ず確認する

---

## 3. Max Loss Limit（最大損失限度額）のイメージ

### Max Loss との関係

- **中身の概念は Max Loss とほぼ同じ**
- "Limit" という語で **「ここを超えてはいけない、厳格な上限」** というニュアンスを強調しているだけのことも多い

### ポイント

- 「Max Loss」と「Max Loss Limit」が両方出てきたら：
  - **別ルールなのか、単なる言い換えなのか** を文脈で確認する
  - 多くは **「言い換え」または「金額で書き直したもの」** に過ぎない
  - 特に気にしなくてよい

---

## 4. Max Drawdown（最大下落幅）のイメージ

### コンセプト

- **「基準 = ピーク（最高値）からどこまで落ちたらアウトか」** を決めるルール
- 「何をピークとみなすか」で挙動が大きく変わる

危険度小 → 危険度大：**Balance Based ＜ Equity Based ＜ Balance or Equity at EOD ＜ Intraday**

### Static 型（初期口座を基準に固定）

前提：
- 初期口座：$100,000
- Max Drawdown：10%（= $10,000）

```
Equity（有効証拠金）

120k ─────────────────────   利益が出ても
110k ─────────────────────   Max DD ラインは動かない（Static）
100k ─────────────────────   初期口座
 90k ─────────────────────   ← Max Drawdown ライン（-10%）

時系列 → → →
```

どれだけピークが上がっても「90kを割ったらOUT」という判定。

### Trailing 型（追随型）

前提：
- 初期口座：$100,000
- Max Drawdown：10%
- **Trailing・Equity Based**（ピーク Equity を基準に、ラインが追いかけて上がる）

```
Equity

130k ─────▲───  ← 新しいピーク（130k）
           │
120k ─▲───│──────────────
       │   │
       │   │  Trailing Max DD ライン
       ▼   ▼
108k ──●────────────────  ← 120k の 10% 下
           ●────────────  ← 130k の 10% 下（117k）※さらに引き上がる

時系列 → → →
```

Equity が新しい高値をつけると、**ピーク値 − 10%** のラインが **上へ追随** する。  
その結果：**利益が増えれば増えるほど、「許される下落幅」は金額ベースでは狭くなる**

### 要注意ポイント

Max Drawdown は、以下をセットで確認する：

- **Max Loss Type** — Static / Trailing のどちらか
- **基準の種類** — Balance Based / Equity Based / Balance or Equity at EOD / Interday など
- 特に **Trailing＋Intraday** の組み合わせは失格リスクが高い

---

## 5. 3つの関係性（全体図）

```
【損失に関するルール全体】

1. 累計損失の上限
   - Max Loss
   - Max Loss Limit
   → 「口座全体として最終的にここまで負けたらアウト」という上限額

2. 下落幅（ドローダウン）の上限
   - Max Drawdown
   → 「ピークからここまで落ちたらアウト」という下落幅ルール
      ・Static：基準固定
      ・Trailing：基準が利益に合わせて上昇
```

---

## 6. チェックリスト

Prop Firm のChallengeを選ぶ際には最低限、次の4点をメモしておく：

1. **Max Loss / Max Loss Limit** — Static / Trailing のどちらか
2. **Max Drawdown**
   - パーセンテージはいくらか？
   - 基準は Balance / Equity / EOD / Intraday のどれか？
   - 利益を出したとき、**DD ラインは動くか / 動かないか？**
3. **Daily Loss / Daily Drawdown が別にあるか** — 日次の上限と全体のMax Loss / Max DDが**両方ある**ことが多い
4. **攻略メモ** — Interday型の場合、利益が出たら即利確
