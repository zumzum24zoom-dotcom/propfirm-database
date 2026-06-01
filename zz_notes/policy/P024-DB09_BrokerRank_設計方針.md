---
state: 有効
type: 仕様
must_read: false
---

## 要点
ブローカーの規制情報（公的事実）を軸に提携Prop Firmの信頼性を間接評価するDB設計。

- 登録原則: 公的DBで検証できる情報のみ
- 信頼性判断軸: Regulator_Top（FCA/ASIC等）の数
- Reg_Top_Count = Top のみカウント（Mid・オフショアは混ぜない）
- Reg_Top_Count=0 は信頼性に疑義あり
