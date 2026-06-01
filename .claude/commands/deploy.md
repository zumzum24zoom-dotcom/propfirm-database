Hugo ビルドして Netlify へデプロイする。

以下の手順で実行：
1. `hugo` コマンドでビルド（エラーがあれば報告して停止）
2. `netlify status` で接続確認
3. `netlify deploy --prod` で本番デプロイ
4. デプロイ完了URLを報告する
