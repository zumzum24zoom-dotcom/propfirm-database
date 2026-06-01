---
state: 有効
type: 決定事項
must_read: true
---

## 要点（Hugo時代: 旧Cron+KV方式の後継）
定期更新が必要なデータ（クーポン等）は GitHub Actions Cron + Netlify Deploy 方式で配信する。

- GitHub Actions: 毎月3日・18日 Playwright でクーポン取得
- 取得結果 → data/firms/*.json 更新 → Netlify 自動デプロイ
- 静的ファイル配信のため KV 不要

## 参照
scripts/extract-coupons.mjs / .github/workflows/
