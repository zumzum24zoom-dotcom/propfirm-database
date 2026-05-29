import React, { useState } from 'react';

function TodayBiasTool() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('top10');
  const [filterPattern, setFilterPattern] = useState('all');
  const [csvFile, setCsvFile] = useState(null);

  // CSV読み込み
  const handleCSVUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setCsvFile(file);
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const csv = e.target.result;
        const parsed = parseCSV(csv);
        setResults(parsed);
        setError(null);
      } catch (err) {
        setError('CSV解析エラー: ' + err.message);
      }
    };
    reader.readAsText(file);
  };

  // CSV解析
  const parseCSV = (csv) => {
    const lines = csv.trim().split('\n');
    const headers = lines[0].split(',');
    
    const ranking = [];
    
    for (let i = 1; i < lines.length; i++) {
      const values = parseCSVLine(lines[i]);
      
      if (values.length < 9) continue;
      
      const prevOHLC = JSON.parse(values[7] || '{}');
      const todayOHLC = JSON.parse(values[8] || '{}');
      
      // パターンから内部コード推定
      const pattern = inferPatternCode(values[2], values[5]);
      
      ranking.push({
        symbol: values[1],
        pattern: pattern,
        n: parseInt(values[3]) || 0,
        confidence: parseFloat(values[4]) || 0,
        action: values[6],
        prevDay: prevOHLC,
        today: todayOHLC
      });
    }
    
    return {
      timestamp: new Date().toISOString(),
      ranking: ranking,
      stats: {
        totalCoins: 105,
        analyzed: ranking.length,
        withSignal: ranking.filter(r => r.pattern !== 'RG').length,
        rangeCoins: ranking.filter(r => r.pattern === 'RG').length
      }
    };
  };

  // CSV行解析（カンマ・引用符考慮）
  const parseCSVLine = (line) => {
    const values = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      const nextChar = line[i + 1];
      
      if (char === '"' && nextChar === '"' && inQuotes) {
        // ダブルクォートのエスケープ ("")
        current += '"';
        i++; // 次の文字をスキップ
      } else if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current);
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current);
    
    return values.map(v => v.trim());
  };

  // パターン内部コード推定
  const inferPatternCode = (patternLabel, biasSymbol) => {
    // バイアスシンボルから推定
    if (biasSymbol === '▲') return 'BC';
    if (biasSymbol === '△') return 'BuR';
    if (biasSymbol === '▼') return 'BR';
    if (biasSymbol === '▽') return 'BeR';
    if (biasSymbol === '■') return 'RG';
    
    // ラベルから推定（フォールバック）
    if (patternLabel === '継続') {
      return 'BC'; // 仮定
    }
    if (patternLabel === '反転') {
      return 'BuR'; // 仮定
    }
    if (patternLabel === 'レンジ') {
      return 'RG';
    }
    
    return 'RG';
  };

  // 個別銘柄のローソク足2本（実データ反映）
  const CandleChart = ({ prevDay, today, pattern }) => {
    const width = 120;
    const height = 80;
    const padding = 10;
    const chartHeight = height - padding * 2;
    
    // 価格範囲計算
    const allPrices = [
      prevDay.high, prevDay.low, prevDay.open, prevDay.close,
      today.high, today.low, today.open, today.close
    ];
    const maxPrice = Math.max(...allPrices);
    const minPrice = Math.min(...allPrices);
    const priceRange = maxPrice - minPrice || 1; // ゼロ除算防止
    
    // 価格→Y座標変換
    const priceToY = (price) => {
      return padding + ((maxPrice - price) / priceRange * chartHeight);
    };
    
    // PDH/PDL
    const pdh = prevDay.high;
    const pdl = prevDay.low;
    const pdhY = priceToY(pdh);
    const pdlY = priceToY(pdl);
    
    // ローソク足描画関数
    const drawCandle = (candle, x) => {
      const isBullish = candle.close >= candle.open;
      const color = isBullish ? '#10b981' : '#ef4444';
      
      const highY = priceToY(candle.high);
      const lowY = priceToY(candle.low);
      const openY = priceToY(candle.open);
      const closeY = priceToY(candle.close);
      
      const bodyTop = Math.min(openY, closeY);
      const bodyBottom = Math.max(openY, closeY);
      const bodyHeight = bodyBottom - bodyTop || 1; // 最小1px
      
      return (
        <g key={x}>
          {/* 上ヒゲ */}
          {candle.high > Math.max(candle.open, candle.close) && (
            <line 
              x1={x} y1={highY} 
              x2={x} y2={bodyTop}
              stroke={color} 
              strokeWidth="1.5"
            />
          )}
          
          {/* 下ヒゲ */}
          {candle.low < Math.min(candle.open, candle.close) && (
            <line 
              x1={x} y1={bodyBottom} 
              x2={x} y2={lowY}
              stroke={color} 
              strokeWidth="1.5"
            />
          )}
          
          {/* 実体 */}
          <rect 
            x={x - 8} 
            y={bodyTop}
            width="16" 
            height={bodyHeight}
            fill={isBullish ? color : 'white'}
            stroke={color}
            strokeWidth="2"
          />
        </g>
      );
    };
    
    // パターンに応じた色
    const patternColor = pattern === 'BC' || pattern === 'BuR' ? '#10b981' : 
                         pattern === 'BR' || pattern === 'BeR' ? '#ef4444' : '#6b7280';
    
    return (
      <svg width={width} height={height} style={{ display: 'block' }}>
        {/* PDH ライン */}
        <line 
          x1="0" y1={pdhY} 
          x2={width} y2={pdhY}
          stroke="#94a3b8" 
          strokeWidth="1" 
          strokeDasharray="3,2"
        />
        <text x="2" y={pdhY - 2} fontSize="9" fill="#64748b">PDH</text>
        
        {/* PDL ライン */}
        <line 
          x1="0" y1={pdlY} 
          x2={width} y2={pdlY}
          stroke="#94a3b8" 
          strokeWidth="1" 
          strokeDasharray="3,2"
        />
        <text x="2" y={pdlY + 10} fontSize="9" fill="#64748b">PDL</text>
        
        {/* 前日ローソク足 */}
        {drawCandle(prevDay, 35)}
        
        {/* 当日ローソク足 */}
        {drawCandle(today, 85)}
      </svg>
    );
  };

  // パターン説明用の標準ローソク足
  const PatternExample = ({ pattern }) => {
    const examples = {
      BC: { 
        prev: { open: 100, high: 110, low: 95, close: 105 },
        today: { open: 105, high: 120, low: 103, close: 118 },
        desc: '強気継続'
      },
      BR: { 
        prev: { open: 100, high: 110, low: 95, close: 105 },
        today: { open: 98, high: 100, low: 85, close: 88 },
        desc: '弱気継続'
      },
      BuR: { 
        prev: { open: 100, high: 110, low: 95, close: 105 },
        today: { open: 98, high: 115, low: 90, close: 112 },
        desc: '強気反転'
      },
      BeR: { 
        prev: { open: 100, high: 110, low: 95, close: 105 },
        today: { open: 108, high: 115, low: 102, close: 104 },
        desc: '弱気拒絶'
      },
      RG: { 
        prev: { open: 100, high: 110, low: 95, close: 105 },
        today: { open: 102, high: 108, low: 98, close: 103 },
        desc: 'レンジ'
      }
    };
    
    const ex = examples[pattern];
    
    return (
      <div>
        <CandleChart prevDay={ex.prev} today={ex.today} pattern={pattern} />
        <div style={{ textAlign: 'center', fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>
          {ex.desc}
        </div>
      </div>
    );
  };

  // パターン表示名取得
  const getPatternLabel = (pattern) => {
    const labels = {
      BC: '継続',
      BuR: '反転',
      BR: '継続',
      BeR: '反転',
      RG: 'レンジ'
    };
    return labels[pattern] || pattern;
  };

  // バイアスアイコン取得（SVG）
  const getBiasIcon = (pattern) => {
    const size = 20;
    const icons = {
      BC: ( // ▲ 青塗り
        <svg width={size} height={size} viewBox="0 0 20 20">
          <polygon points="10,3 17,15 3,15" fill="#3b82f6" />
        </svg>
      ),
      BuR: ( // △ 青輪郭
        <svg width={size} height={size} viewBox="0 0 20 20">
          <polygon points="10,3 17,15 3,15" fill="none" stroke="#3b82f6" strokeWidth="2" />
        </svg>
      ),
      BR: ( // ▼ 赤塗り
        <svg width={size} height={size} viewBox="0 0 20 20">
          <polygon points="10,17 17,5 3,5" fill="#ef4444" />
        </svg>
      ),
      BeR: ( // ▽ 赤輪郭
        <svg width={size} height={size} viewBox="0 0 20 20">
          <polygon points="10,17 17,5 3,5" fill="none" stroke="#ef4444" strokeWidth="2" />
        </svg>
      ),
      RG: ( // ■ グレー
        <svg width={size} height={size} viewBox="0 0 20 20">
          <rect x="4" y="4" width="12" height="12" fill="#6b7280" />
        </svg>
      )
    };
    return icons[pattern] || null;
  };

  // 全銘柄モックデータ生成（実データ風）
  const generateMockData = () => {
    const patterns = ['BC', 'BR', 'BuR', 'BeR', 'RG'];
    const candleTypes = ['A陽', 'B陰'];
    const symbols = [
      'BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'DOT', 'LINK', 'UNI',
      'AAVE', 'ALGO', 'APE', 'APT', 'ARB', 'ATOM', 'AXS', 'BCH', 'BLUR', 'BONK',
      'CRV', 'FET', 'FIL', 'FLOW', 'GRT', 'ICP', 'IMX', 'INJ', 'JUP', 'LDO',
      'LTC', 'MATIC', 'NEAR', 'OP', 'PEPE', 'RENDER', 'RUNE', 'SAND', 'SEI', 'SHIB',
      'SNX', 'STX', 'SUI', 'TIA', 'TON', 'TRB', 'WIF', 'WLD', 'ONDO', 'PYTH'
    ];

    return symbols.map(symbol => {
      const basePrice = 50 + Math.random() * 100;
      const pattern = patterns[Math.floor(Math.random() * patterns.length)];
      
      // 前日ローソク足生成
      const prevOpen = basePrice;
      const prevRange = basePrice * 0.15;
      const prevHigh = prevOpen + Math.random() * prevRange;
      const prevLow = prevOpen - Math.random() * prevRange;
      const prevClose = prevLow + Math.random() * (prevHigh - prevLow);
      
      const prevDay = {
        open: parseFloat(prevOpen.toFixed(2)),
        high: parseFloat(prevHigh.toFixed(2)),
        low: parseFloat(prevLow.toFixed(2)),
        close: parseFloat(prevClose.toFixed(2))
      };
      
      // 当日ローソク足生成（パターンに応じて）
      let todayOpen, todayHigh, todayLow, todayClose;
      
      switch(pattern) {
        case 'BC': // 終値がPDH超え
          todayOpen = prevClose + (Math.random() - 0.3) * prevRange * 0.2;
          todayClose = prevDay.high + Math.random() * prevRange * 0.3;
          todayHigh = Math.max(todayOpen, todayClose) + Math.random() * prevRange * 0.1;
          todayLow = Math.min(todayOpen, todayClose) - Math.random() * prevRange * 0.05;
          break;
          
        case 'BR': // 終値がPDL割れ
          todayOpen = prevClose + (Math.random() - 0.7) * prevRange * 0.2;
          todayClose = prevDay.low - Math.random() * prevRange * 0.3;
          todayLow = Math.min(todayOpen, todayClose) - Math.random() * prevRange * 0.1;
          todayHigh = Math.max(todayOpen, todayClose) + Math.random() * prevRange * 0.05;
          break;
          
        case 'BuR': // 安値PDL下抜け＆終値PDL以上
          todayOpen = prevDay.low + (Math.random() - 0.5) * prevRange * 0.1;
          todayLow = prevDay.low - Math.random() * prevRange * 0.2;
          todayClose = prevDay.low + Math.random() * prevRange * 0.4;
          todayHigh = todayClose + Math.random() * prevRange * 0.2;
          break;
          
        case 'BeR': // 高値PDH上抜け＆終値PDH以下
          todayOpen = prevDay.high - (Math.random() - 0.5) * prevRange * 0.1;
          todayHigh = prevDay.high + Math.random() * prevRange * 0.2;
          todayClose = prevDay.high - Math.random() * prevRange * 0.4;
          todayLow = todayClose - Math.random() * prevRange * 0.2;
          break;
          
        default: // RG
          todayOpen = prevLow + Math.random() * (prevHigh - prevLow);
          todayClose = prevLow + Math.random() * (prevHigh - prevLow);
          todayHigh = Math.max(todayOpen, todayClose) + Math.random() * prevRange * 0.05;
          todayLow = Math.min(todayOpen, todayClose) - Math.random() * prevRange * 0.05;
      }
      
      const today = {
        open: parseFloat(todayOpen.toFixed(2)),
        high: parseFloat(todayHigh.toFixed(2)),
        low: parseFloat(todayLow.toFixed(2)),
        close: parseFloat(todayClose.toFixed(2))
      };
      
      const candleType = today.close >= today.open ? 'A陽' : 'B陰';
      const n = Math.floor(Math.random() * 20) + 10;
      const baseRate = 45 + Math.random() * 30;
      const confidence = n >= 15 ? baseRate : baseRate * 0.9;
      const direction = (pattern === 'BC' || pattern === 'BuR') ? '↑' : '↓';
      
      let action = '様子見';
      if (pattern !== 'RG') {
        if (confidence >= 65) action = direction === '↑' ? 'BUY推奨' : 'SELL推奨';
        else if (confidence >= 55) action = direction === '↑' ? 'BUY検討' : 'SELL検討';
      }

      return {
        symbol,
        pattern,
        candleType,
        n,
        confidence: parseFloat(confidence.toFixed(1)),
        direction,
        action,
        prevDay,
        today
      };
    }).sort((a, b) => b.confidence - a.confidence);
  };

  const mockData = {
    timestamp: new Date().toISOString(),
    ranking: generateMockData(),
    stats: {
      totalCoins: 105,
      analyzed: 50,
      withSignal: 42,
      rangeCoins: 8
    }
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      setResults(mockData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredData = () => {
    if (!results) return [];
    
    let data = viewMode === 'top10' 
      ? results.ranking.slice(0, 10)
      : results.ranking;
    
    if (filterPattern !== 'all') {
      data = data.filter(item => item.pattern === filterPattern);
    }
    
    return data;
  };

  return (
    <div style={{ 
      fontFamily: 'system-ui, -apple-system, sans-serif',
      maxWidth: '1400px',
      margin: '0 auto',
      padding: '20px',
      background: '#f9fafb',
      minHeight: '100vh'
    }}>
      {/* ヘッダー */}
      <div style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '30px',
        borderRadius: '12px',
        marginBottom: '30px'
      }}>
        <h1 style={{ margin: '0 0 10px 0', fontSize: '32px' }}>今日のバイアス</h1>
        <p style={{ margin: 0, opacity: 0.9 }}>暗号資産105銘柄のSMCバイアス分析ツール（実データ反映ローソク足表示）</p>
      </div>

      {/* パターン説明パネル */}
      <div style={{
        background: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#1f2937' }}>
          📊 SMCバイアスパターン（前日→当日）
        </h3>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '16px'
        }}>
          {['BC', 'BR', 'BuR', 'BeR', 'RG'].map(pattern => (
            <div key={pattern} style={{
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '12px',
              background: '#f9fafb'
            }}>
              <PatternExample pattern={pattern} />
            </div>
          ))}
        </div>
      </div>

      {/* 実行ボタン + CSV取り込み */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '20px',
        alignItems: 'center'
      }}>
        <button
          onClick={handleRun}
          disabled={loading}
          style={{
            background: loading ? '#9ca3af' : '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            fontSize: '16px',
            borderRadius: '8px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: '600',
            flex: '1'
          }}
        >
          {loading ? '分析中...' : 'データ取得（API）'}
        </button>
        
        <div style={{ position: 'relative', flex: '1' }}>
          <input
            type="file"
            accept=".csv"
            onChange={handleCSVUpload}
            style={{ display: 'none' }}
            id="csv-upload"
          />
          <label
            htmlFor="csv-upload"
            style={{
              display: 'block',
              background: '#10b981',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              fontSize: '16px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600',
              textAlign: 'center'
            }}
          >
            📁 CSVファイルを読み込む
          </label>
          {csvFile && (
            <div style={{
              fontSize: '12px',
              color: '#6b7280',
              marginTop: '4px',
              textAlign: 'center'
            }}>
              {csvFile.name}
            </div>
          )}
        </div>
      </div>

      {error && (
        <div style={{
          background: '#fee2e2',
          color: '#991b1b',
          padding: '16px',
          borderRadius: '8px',
          marginBottom: '20px'
        }}>
          エラー: {error}
        </div>
      )}

      {results && (
        <div>
          {/* 統計サマリー */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            marginBottom: '20px'
          }}>
            <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>分析銘柄</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#1f2937' }}>
                {results.stats.analyzed}/{results.stats.totalCoins}
              </div>
            </div>
            <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>シグナル検出</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#1f2937' }}>
                {results.stats.withSignal}銘柄
              </div>
            </div>
            <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>レンジ相場</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#1f2937' }}>
                {results.stats.rangeCoins}銘柄
              </div>
            </div>
          </div>

          {/* フィルターコントロール */}
          <div style={{
            background: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            padding: '16px',
            marginBottom: '20px',
            display: 'flex',
            gap: '16px',
            flexWrap: 'wrap',
            alignItems: 'center'
          }}>
            <div>
              <label style={{ fontSize: '14px', color: '#6b7280', marginRight: '8px' }}>表示:</label>
              <button
                onClick={() => setViewMode('top10')}
                style={{
                  background: viewMode === 'top10' ? '#3b82f6' : 'white',
                  color: viewMode === 'top10' ? 'white' : '#1f2937',
                  border: '1px solid #e5e7eb',
                  padding: '6px 16px',
                  borderRadius: '6px',
                  marginRight: '8px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                TOP10
              </button>
              <button
                onClick={() => setViewMode('all')}
                style={{
                  background: viewMode === 'all' ? '#3b82f6' : 'white',
                  color: viewMode === 'all' ? 'white' : '#1f2937',
                  border: '1px solid #e5e7eb',
                  padding: '6px 16px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                全銘柄
              </button>
            </div>

            <div>
              <label style={{ fontSize: '14px', color: '#6b7280', marginRight: '8px' }}>パターン:</label>
              {[
                { key: 'all', label: '全て' },
                { key: 'BC', label: '強気継続' },
                { key: 'BuR', label: '強気反転' },
                { key: 'BR', label: '弱気継続' },
                { key: 'BeR', label: '弱気反転' },
                { key: 'RG', label: 'レンジ' }
              ].map(p => (
                <button
                  key={p.key}
                  onClick={() => setFilterPattern(p.key)}
                  style={{
                    background: filterPattern === p.key ? '#3b82f6' : 'white',
                    color: filterPattern === p.key ? 'white' : '#1f2937',
                    border: '1px solid #e5e7eb',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    marginRight: '8px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* ランキングテーブル */}
          <div style={{
            background: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            overflow: 'hidden'
          }}>
            <div style={{
              background: '#1f2937',
              color: 'white',
              padding: '16px 20px',
              fontSize: '18px',
              fontWeight: '600'
            }}>
              📊 {viewMode === 'top10' ? 'TOP10推奨銘柄' : `全銘柄 (${getFilteredData().length}件)`}
            </div>
            <div style={{ overflowX: 'auto', maxHeight: viewMode === 'all' ? '600px' : 'none', overflowY: viewMode === 'all' ? 'auto' : 'visible' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead style={{ position: 'sticky', top: 0, background: '#f9fafb', zIndex: 1 }}>
                  <tr>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb' }}>銘柄</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e5e7eb' }}>ローソク足</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e5e7eb' }}>パターン</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e5e7eb' }}>N</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e5e7eb' }}>信頼度</th>
                    <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #e5e7eb' }}>バイアス</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb' }}>アクション</th>
                  </tr>
                </thead>
                <tbody>
                  {getFilteredData().map((item, index) => (
                    <tr key={index} style={{ 
                      background: index % 2 === 0 ? 'white' : '#f9fafb',
                      borderBottom: '1px solid #e5e7eb'
                    }}>
                      <td style={{ padding: '12px', fontWeight: '600' }}>{item.symbol}</td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <CandleChart prevDay={item.prevDay} today={item.today} pattern={item.pattern} />
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <span style={{
                          background: item.pattern === 'BC' || item.pattern === 'BuR' ? '#dbeafe' : item.pattern === 'RG' ? '#f3f4f6' : '#fee2e2',
                          color: item.pattern === 'BC' || item.pattern === 'BuR' ? '#1e40af' : item.pattern === 'RG' ? '#6b7280' : '#991b1b',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: '600'
                        }}>
                          {getPatternLabel(item.pattern)}
                        </span>
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', color: '#6b7280', fontSize: '13px' }}>{item.n}</td>
                      <td style={{ padding: '12px', textAlign: 'center', fontWeight: '600' }}>
                        {item.confidence}%
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        {getBiasIcon(item.pattern)}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          background: item.action.includes('推奨') ? '#10b981' : item.action.includes('検討') ? '#f59e0b' : '#6b7280',
                          color: 'white',
                          padding: '4px 12px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: '600'
                        }}>
                          {item.action}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* フッター */}
          <div style={{
            marginTop: '20px',
            padding: '16px',
            background: 'white',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            fontSize: '12px',
            color: '#6b7280'
          }}>
            <div><strong>更新:</strong> {new Date(results.timestamp).toLocaleString('ja-JP')}</div>
            <div style={{ marginTop: '4px' }}>
              <strong>統計:</strong> 180日 | <strong>データ:</strong> CoinGecko + Crypto.com | <strong>信頼度:</strong> baseRate × nAdjustment（距離除外）
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TodayBiasTool;
