# pfd-coupon-fetcher — セットアップ手順

## 概要

毎月1日 00:00 UTC に全Firmの公式サイトを巡回し、クーポンコードを自動取得する Cloudflare Worker。  
取得結果は `data/firms/*.json` の `"クーポン"` フィールドに書き込まれ、GitHub にバッチコミットされる。  
Netlify が commit を検知して自動デプロイするため、サイトに反映される。

## 前提

- Cloudflare アカウント（無料可）
- `wrangler` CLI (`npm install -g wrangler`)
- GitHub Personal Access Token（`Contents: Read & Write` 権限）
- Anthropic API キー

## デプロイ手順

```bash
cd 01_tools/coupon-fetcher

# 1. Cloudflare にログイン
wrangler login

# 2. Secrets を登録（.toml に書かずここで設定）
wrangler secret put ANTHROPIC_KEY
wrangler secret put GITHUB_TOKEN
wrangler secret put TRIGGER_SECRET   # 任意の文字列（手動トリガー用）

# 3. デプロイ
wrangler deploy
```

## 手動トリガー

デプロイ後、以下のURLにアクセスすると即座に実行できる:

```
https://pfd-coupon-fetcher.<your-subdomain>.workers.dev/?secret=YOUR_TRIGGER_SECRET
```

レスポンス `{"status":"started"}` が返ればバックグラウンドで実行中。

## 動作フロー

1. GitHub API で `data/firms/*.json` を全件取得
2. 各Firmの `アフィリエイトURL`（なければ `公式URL`）を取得
3. 各サイトのHTMLを先頭8KBフェッチ
4. Claude Haiku にクーポンコードの抽出を依頼
5. 現在値と差分がある場合のみ更新リストに追加
6. 全更新を1コミットで GitHub にバッチ書き込み
7. Netlify が自動デプロイ

## 注意事項

- **JSレンダリング非対応**: React/Angular等でDOMを動的生成するサイトは、取得したHTMLにクーポンが含まれない場合がある。その場合は手動入力が必要。
- **Cloudflare 無料プランの制限**: scheduled Worker は CPU 30秒制限。34社フル実行に必要な時間はI/O待ちが主なため通常は収まるが、全社が重い場合は有料プランを検討。
- **費用**: Claude Haiku は1回の実行あたり約 $0.01（34社×8KB入力）。
- **クーポン期限管理**: Worker は期限切れのコードを自動削除しない。`expires` フィールドを見てHugo側でフィルタするか、別途クリーンアップが必要。
