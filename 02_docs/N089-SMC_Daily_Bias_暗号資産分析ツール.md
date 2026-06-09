# 今日のバイアス - 暗号資産SMC分析ツール（完成）

- **ID**: N089
- **状態**: 移設
- **目的**: 暗号資産105銘柄のSMC（Smart Money Concepts）バイアス分析。Google Spreadsheet + GAS + React Artifactで毎日自動更新
- **対象**: https://docs.google.com/spreadsheets/d/1LMDtnJO2NWt2ynrWRznwOCmCzNz15aOjx43O0rSreNQ
- **完了日**: 2026-05-17
- **Notion**: https://app.notion.com/p/363660a529e281a7b512c8907eab2448

---

## システム概要

暗号資産105銘柄のSMC（Smart Money Concepts）バイアス分析ツール。

**構成**: Google Spreadsheet + Google Apps Script (GAS) + React Artifact  
**データソース**: CoinGecko Demo API  
**更新頻度**: 毎日自動（6:00 JST）

---

## 完成成果物

### 1. Google Spreadsheet

**URL**: https://docs.google.com/spreadsheets/d/1LMDtnJO2NWt2ynrWRznwOCmCzNz15aOjx43O0rSreNQ

**4シート構成**:

- **RawData**: 生OHLCデータ（現在225行: 5銘柄×45日）
- **DailyBias**: バイアス判定結果（220行）
- **Stats**: パターン別統計（2件: N≥10のみ）
- **TodayRanking**: 本日ランキング（データ蓄積後に生成）

### 2. Google Apps Script (GAS)

**ファイル**: `DailyUpdate_GAS_With180Days.js` (20KB)

**主要関数**:

- `initialLoad180Days()` - 初回データ投入（実行済み）
- `dailyUpdate()` - 毎日自動更新（トリガー設定済み: 毎日6:00）
- `exportTodayRankingCSV()` - CSV出力

**実行状況**:

- ✅ 初回180日投入完了（2026-05-17実行）
- ✅ 毎日自動トリガー設定完了
- ✅ 5銘柄×45日分データ取得成功

### 3. React Artifact UI

**ファイル**: `TodayBiasTool_Complete_Fixed.jsx` (27KB)  
**配置**: `01_tools/_archive/other-tools/TodayBiasTool_Complete_Fixed.jsx`

**実装機能**:

- ローソク足2本表示（実データ反映: OHLC値から正確に描画）
- PDH/PDL点線表示
- パターン日本語表記: 継続/反転/レンジ
- バイアス列: ▲△▼▽■（色付き図形）
- CSV取り込み機能（ダブルクォートエスケープ対応）
- TOP10/全銘柄切り替え
- パターンフィルター（6種）

**テーブル構成（7列）**:  
銘柄 | ローソク足 | パターン | N | 信頼度 | バイアス | アクション

---

## API・認証情報

### CoinGecko Demo API

- **APIキー**: `CG-1n7eVhDbotHKaqQkGQCUt9Q2`
- **レート制限**: 100リクエスト/分
- **月間上限**: 10,000リクエスト
- **Root URL**: `https://api.coingecko.com/api/v3`

---

## 運用フロー

### 毎日の自動実行

```
毎朝6:00 GAS dailyUpdate() 自動実行
  ↓
1. CoinGecko API → 当日OHLC取得（5銘柄）
2. バイアス判定（BC/BR/BuR/BeR/RG）
3. 前日Success更新（翌日高値・安値で検証）
4. Stats再計算（180日、N≥10フィルター）
5. TodayRankingシート更新
```

### 手動確認・CSV出力

```
1. Spreadsheet TodayRankingシート確認
2. GAS関数 exportTodayRankingCSV() 実行
3. CSV出力 → テキストファイル保存
4. React ArtifactにCSVアップロード
5. 視覚的分析・トレード判断
```

---

## 統計検証結果

### 距離除外の決定

**結論**: **距離を信頼度計算から完全除外**

**統計的証拠**（10銘柄×180日、4パターン検証）:

- BC: 0-2% 59.3% vs 2-5% 61.6% → 信頼区間重なる（無意味）
- BR: 0-2% 58.8% vs 2-5% 71.4% → 有意差あり（唯一の例外、特別扱いしない）
- BuR: 0-2% 42.7% vs 2-5% 48.4% → 無意味
- BeR: 0-2% 55.9% vs 2-5% 65.1% → むしろ小陰線が信頼できる（N少）

**理由**: 75%のパターンで距離無関係。SMC理論の本質は「位置」であり「大きさ」ではない。

### 確定した信頼度計算式

```javascript
confidence = baseRate × nAdjustment
// baseRate: パターン×陰陽の過去180日成功率
// nAdjustment: N≥15→1.0, N=10-14→0.9, N<10→除外
// distanceAdjustment: なし（完全除外）
```

---

## 技術的詳細

### CoinGecko API仕様

- **使用エンドポイント**: `/coins/{coinId}/ohlc`
- **パラメータ**: `?vs_currency=usd&days=180&x_cg_demo_api_key=KEY`
- **レスポンス形式**: `[[timestamp, open, high, low, close], ...]`（新しい順）
- **制限事項**: `days="180"` でも実際は約45日分のみ返却される

### バイアス分類ロジック

```javascript
if (todayCandle.close > pdh) {
  pattern = 'BC'; // 強気継続
} else if (todayCandle.close < pdl) {
  pattern = 'BR'; // 弱気継続
} else if (todayCandle.low < pdl && todayCandle.close >= pdl) {
  pattern = 'BuR'; // 強気反転
} else if (todayCandle.high > pdh && todayCandle.close <= pdh) {
  pattern = 'BeR'; // 弱気反転
} else {
  pattern = 'RG'; // レンジ
}
```

---

## 今後の拡張

### 優先度: 高

1. **105銘柄マッピング追加**
   - ファイル: `tradeify_crypto_105_mapping.json` (14KB)
   - CONFIG.SYMBOLS配列を拡張
2. **180日完全データ取得**
   - 現在45日 → 180日に拡張

### 優先度: 中

1. **記事執筆**: 「【検証結果】大陽線・大陰線はトリガーとして役に立たない」
2. **Notion DB連携**: 統計・ランキングをNotion DBに自動記録

---

## 成果物管理

| ファイル | サイズ | 場所 |
|---|---|---|
| `DailyUpdate_GAS_With180Days.js` | 20KB | プロジェクトファイル |
| `TodayBiasTool_Complete_Fixed.jsx` | 27KB | `01_tools/_archive/other-tools/` |
| `spreadsheet_schema.js` | 7.1KB | outputs/ |
| `distance_verification_results.js` | 9.9KB | outputs/ |
| `tradeify_crypto_105_mapping.json` | 14KB | outputs/ |

---

## 技術選択理由

**Google Spreadsheet選択**:
- 数値計算に最適
- GAS無料自動実行
- 集計が楽（配列数式・QUERY関数）
- API書き込み高速
- CSV出力が容易

**Notion DBを使わなかった理由**:
- 数値計算・集計がSpreadsheetより遅い
- API書き込みコスト高
- CSV出力が複雑
