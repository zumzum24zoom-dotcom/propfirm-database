---
type: plans
title: "2-Step PRO V2"
slug: "2-step-pro-v2"
firm: "top-one-trader"
---

コード変更不要です。既存の「表取込」で取り込めます。

**表取込の形式（`| 利益目標 | C | F | diff | 詳細 |`）で貼るだけ：**

---

**1-Step FLASH / 1-Step NOVA / 2-Step PLUS / Instant Funding / Instant Prime（共通）：**
```
| 項目 | Challenge | Funded | 差分 | 詳細 |
|---|---|---|---|---|
| 利益目標 | — | 2% | — | 最低出金額。初期残高の2%の利益が出金の条件 |
```

**2-Step PRO V2のみ：**
```
| 項目 | Challenge | Funded | 差分 | 詳細 |
|---|---|---|---|---|
| 利益目標 | — | 3% | — | 最低出金額。初期残高の3%の利益が出金の条件（例：$50,000口座→$1,500） |
```

---

**NotebookLM への指示としては：**

> 「利益目標（Funded）の値を `| 利益目標 | Challenge値 | Funded値 | 差分 | 詳細 |` の形式で出力してください」

と書けば上記と同じ形式で出力されます。

**使い方：**
1. 各プランの DBP-02 タブを開く
2. 上記テーブルを取込エリアに貼り付け
3. 「表取込」→ `rd_target`（利益目標）スロットに格納

Challenge列（—）は後で他のデータと一緒に上書きできます。