---
state: 有効
type: 決定事項
must_read: true
---

## 要点
攻略_Firm記事の出金スケジュールwidgetは、Worker独自計算方式（ver.01）を廃止し、記事本文の「最速出金スケジュール（理論値）」テーブルから値をDOMで抽出して描画する方式に転換。

**単一情報源** = !Survey_firmが生成する攻略記事本文のテーブル

## Hugo時代への適用
Widget Maker の PAYOUT_TIMELINE widget も同方針:
- 計算ロジックは Page Maker generateKoryakuPrompt 断面③に集約
- Widget は値の取得 + 描画のみに簡略化
