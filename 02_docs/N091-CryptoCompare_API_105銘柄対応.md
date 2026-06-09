# CryptoCompare API 105銘柄対応（SMC Daily Bias）

- **ID**: N091
- **状態**: 移設
- **目的**: Binance API地域制限回避・105銘柄の暗号資産価格データ取得システム構築
- **対象URL**: https://www.propfirm-challengers.jp/
- **最終更新**: 2026-05-30
- **Notion**: https://app.notion.com/p/364660a529e281f5a2aff9db5aa666d2

---

## 概要

Binance API地域制限（HTTP 451）により、代替データソースとしてCryptoCompare APIを導入。105銘柄（実質108銘柄）の暗号資産価格データを取得し、SMC Daily Biasツールに統合。

## 完了状況

### データ投入結果

- **バイアス計算**: 19,440行完了
- **統計計算**: 613件生成
- **ランキング生成**: 13件生成
- **実行時間**: 約29秒

### 銘柄カバレッジ

- **成功**: 108銘柄
- **失敗**: 1銘柄（FART - CryptoCompare未対応）
- **成功率**: 99.1%

### DoD（検証条件）

- CryptoCompare API統合完了
- 180日データ投入完了（19,440行）
- 統計計算613件・ランキング13件生成確認
- 108/109銘柄稼働（FART除外）
- dailyUpdate()による毎日自動更新機能稼働
- 月間APIコール数3,255回（無料枠100,000回内）

## 技術詳細

### API仕様

- **エンドポイント**: `https://min-api.cryptocompare.com/data/v2/histoday`
- **無料枠**: 100,000コール/月（50 req/sec）
- **月間使用予定**: 3,255コール（初回180日投入 + 日次更新105銘柄×30日）
- **レート制限**: 100ms間隔

### データ構造

- **日次OHLC**: 180日分の履歴データ
- **フォーマット**: `{Data: {Data: [{time, open, high, low, close}]}}`
- **Unix秒→ミリ秒変換**: APIレスポンスを自動変換

### GAS関数

- `initialLoad180Days()`: 初回180日データ一括投入
- `dailyUpdate()`: 毎日自動更新（トリガー設定可能）
- `fetchCryptoCompareOHLC()`: API呼び出しラッパー

## 成果物

### GASコード

- **ファイル名**: `DailyUpdate_GAS_CryptoCompare_105coins.js`
- **スプレッドシート**: `1LMDtnJO2NWt2ynrWRznwOCmCzNz15aOjx43O0rSreNQ`
- **シート構成**:
  - RawData: 生データ（19,440行）
  - DailyBias: バイアス計算結果（613件）
  - Stats: 統計データ
  - TodayRanking: 今日のランキング（13件）

### 108銘柄リスト

BTC, ETH, PAXG, 1INCH, AAVE, ADA, AIXBT, ALGO, APT, ARB, ASTER, ATOM, AVAX, AXS, BAL, BCH, BNB, BONK, BRETT, CAKE, CHZ, COMP, CRV, DEGEN, DOGE, DOT, DYDX, EGLD, ENA, ENJ, ETC, FIL, FLOKI, FLR, FTM, GALA, GLM, GMX, GRASS, GRT, HBAR, HYPE, ICP, IMX, INJ, IP, JTO, JUP, KAITO, KAS, KAVA, LDO, LINK, LIT, LPT, LRC, LTC, MANA, MANTA, MEME, MKR, MOODENG, NEAR, OKB, ONDO, OP, ORDI, PENDLE, PENGU, PEPE, PNUT, POL, POPCAT, PUMP, PYTH, RAY, RENDER, ROSE, RPL, RSR, RUNE, S, SAND, SEI, SHIB, SNX, SOL, STRK, STX, SUI, SUSHI, TAO, TIA, TON, TRUMP, TRX, UNI, VET, VIRTUAL, W, WIF, WLD, XLM, XMR, XPL, XRP, YFI, ZEC

## 注意点

### 除外銘柄

- **FART（Fartcoin）**: CryptoCompareに存在しない（マイナーコイン）
- エラーメッセージ: `CCCAGG market does not exist for this coin pair (FART-USD)`

### 依存関係

- **APIキー**: CONFIG.API.API_KEYに設定必須
- **スプレッドシートID**: CONFIG.SPREADSHEET_IDに設定済み
- **レート制限**: 100ms間隔を遵守（API制限対策）

### 代替案検討履歴

1. **Binance API**: ❌ 地域制限（HTTP 451）
2. **CoinGecko Demo API**: ❌ 3日ラグ
3. **Crypto.com MCP**: ❌ 3日ラグ確認済み
4. **CoinPaprika API**: ❌ 24時間履歴のみ
5. **CoinDesk API**: ❌ 無料プラン廃止（2026年5月21日）
6. **CryptoCompare API**: ✅ 採用

## 次のアクション

### トリガー設定

```javascript
function setupDailyTrigger() {
  ScriptApp.newTrigger('dailyUpdate')
    .timeBased()
    .atHour(6)
    .everyDays(1)
    .create();
}
```

### モニタリング

- 月間APIコール数を監視（無料枠: 100,000コール/月）
- エラー銘柄の追跡（現在: FART除外のみ）
- データ品質チェック（統計計算結果の定期確認）

## 参考資料

- [CryptoCompare API Documentation](https://min-api.cryptocompare.com/documentation)
- [Google Apps Script Spreadsheet Service](https://developers.google.com/apps-script/reference/spreadsheet)
