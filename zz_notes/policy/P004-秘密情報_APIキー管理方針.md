---
state: 有効
type: 運用
must_read: true
---

## 要点
全認証情報は DB_900_Secrets で一元管理（Hugo時代: GitHub Secrets + Netlify env vars）。リスクレベルに応じて保管場所と実装方法を分ける。

- 🟢 低リスク: コード内記載可（公開APIキー等）
- 🟡 中リスク: GitHub Secrets / Netlify env var
- 🔴 高リスク: GitHub Secrets のみ、絶対コミット禁止
