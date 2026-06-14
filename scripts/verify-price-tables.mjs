/**
 * _work/price-collect/{firm}_price.md（収集生データ）と
 * _work/price-collect/wide/{firm}_price.md（変換後）を突き合わせ、
 * 「値の数」「口座サイズ集合」が一致するかを機械的に検証する。
 * 不一致があれば convert-price-tables.mjs での欠落・分裂を意味する。
 */

import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { SIZE_HEADERS, parseTables, normalizePrice, isSizeCell } from './lib/price-table-parse.mjs';

const ROOT     = join(dirname(fileURLToPath(import.meta.url)), '..');
const SRC_DIR  = join(ROOT, '_work', 'price-collect');
const WIDE_DIR = join(SRC_DIR, 'wide');

// 元データ: 全価格テーブルから「値あり（≠—）」セル数と口座サイズ集合を集計
function sourceStats(content) {
  let filled = 0;
  const sizes = new Set();
  for (const t of parseTables(content)) {
    if (!SIZE_HEADERS.has(t.header[0])) continue;
    const cols = t.header.slice(1);
    for (const row of t.rows) {
      const size = (row[0] || '').replace(/\*/g, '').trim();
      if (!isSizeCell(size)) continue;
      sizes.add(size);
      for (let i = 0; i < cols.length; i++) {
        if (normalizePrice(row[i + 1]) !== '—') filled++;
      }
    }
  }
  return { filled, sizes };
}

// 変換後: 横持ち単一テーブルから同様に集計
function wideStats(content) {
  const t = parseTables(content).find(t => SIZE_HEADERS.has(t.header[0]));
  if (!t) return { filled: 0, sizes: new Set() };
  let filled = 0;
  const sizes = new Set();
  for (const row of t.rows) {
    const size = (row[0] || '').replace(/\*/g, '').trim();
    if (!isSizeCell(size)) continue;
    sizes.add(size);
    for (let i = 1; i < row.length; i++) {
      if (normalizePrice(row[i]) !== '—') filled++;
    }
  }
  return { filled, sizes };
}

const files = readdirSync(SRC_DIR).filter(f => f.endsWith('_price.md'));
let allOk = true;
const lines = [];
for (const file of files) {
  const firm = file.replace(/_price\.md$/, '');
  const widePath = join(WIDE_DIR, file);
  if (!existsSync(widePath)) { lines.push(`${firm}: ⚠ wide出力なし`); allOk = false; continue; }

  const src  = sourceStats(readFileSync(join(SRC_DIR, file), 'utf-8'));
  const wide = wideStats(readFileSync(widePath, 'utf-8'));

  const missingSizes = [...src.sizes].filter(s => !wide.sizes.has(s));
  const extraSizes   = [...wide.sizes].filter(s => !src.sizes.has(s));
  const sizeOk   = missingSizes.length === 0 && extraSizes.length === 0;
  const filledOk = src.filled === wide.filled;
  const ok = sizeOk && filledOk;
  if (!ok) allOk = false;

  lines.push(`${firm}: ${ok ? 'OK' : 'NG'}  値=${src.filled}→${wide.filled}  サイズ=${src.sizes.size}→${wide.sizes.size}`);
  if (missingSizes.length) lines.push(`   欠落サイズ: ${missingSizes.join(', ')}`);
  if (extraSizes.length)   lines.push(`   余分サイズ: ${extraSizes.join(', ')}`);
}
console.log(lines.join('\n'));
console.log(allOk ? '\n✅ 全社一致（欠落なし）' : '\n❌ 不一致あり');
process.exit(allOk ? 0 : 1);
