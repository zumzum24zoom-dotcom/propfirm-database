---
state: 有効
type: 方針
must_read: true
---

## 要点（Hugo時代への転換）
旧概念: Wraptas=仕様の正本 / Notion=データの正本

**Hugo時代の正本分離:**
- Hugo themes/pfd/layouts/ = テンプレート・表示仕様の正本
- Page Maker 出力JSON (data/firms/*.json) = データの正本
- CSS/JS/HTML = themes/pfd/static/ に集約

コード・スタイルは特定ページに個別貼付せず、テーマに一元管理。
