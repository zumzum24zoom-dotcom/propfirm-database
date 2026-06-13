/**
 * data/price-collect/{firm}_price.md（収集生データ・プラン別の個別表）を
 * Page Maker の「表取込」が要求する横持ち形式（| 口座サイズ | プラン1 | プラン2 | … |）
 * に機械変換し、data/price-collect/wide/{firm}_price.md に出力する。
 *
 * 出力は Page Maker の取込エリアに貼り付け→「格納」ボタンで priceTable スロットに格納できる。
 * 複数プランにまたがる「価格内訳」列（プロモ/定価/合計/費 等）は heading 付きの列名に展開し、
 * 要確認コメントを出力先頭に付与する。
 */

import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { SIZE_HEADERS, parseRow, parseTables, normalizePrice, sizeNum, isSizeCell } from './lib/price-table-parse.mjs';

const ROOT    = join(dirname(fileURLToPath(import.meta.url)), '..');
const SRC_DIR = join(ROOT, 'data', 'price-collect');
const OUT_DIR = join(SRC_DIR, 'wide');

// >2列テーブルでこれらにマッチする列は「プラン名」ではなく「価格内訳」とみなし、見出し付き列名に展開する
const DENY_RE = /(費|合計|総額|定価|プロモ|通常価格|割引価格|キャンペーン価格|着手金|月額)/;

function buildWideTable(tables) {
  // Pass1: 各テーブル×列 を {heading, planName, colIdx, rows} に分解
  const entries = [];
  for (const t of tables) {
    if (!SIZE_HEADERS.has(t.header[0])) continue; // 価格表以外はスキップ
    const cols = t.header.slice(1);
    if (cols.length === 1) {
      entries.push({ heading: t.heading, planName: t.heading || cols[0], colIdx: 0, rows: t.rows });
    } else {
      cols.forEach((col, idx) => {
        const planName = DENY_RE.test(col) ? `${t.heading || '価格テーブル'} - ${col}` : col;
        entries.push({ heading: t.heading, planName, colIdx: idx, rows: t.rows });
      });
    }
  }
  if (!entries.length) return null;

  // Pass1.5: 異なる見出し由来で同名プランが衝突する場合は見出しを付与して分離
  const headingsByName = new Map();
  for (const e of entries) {
    if (!headingsByName.has(e.planName)) headingsByName.set(e.planName, new Set());
    headingsByName.get(e.planName).add(e.heading);
  }
  for (const e of entries) {
    if (headingsByName.get(e.planName).size > 1) e.planName = `${e.planName} (${e.heading})`;
  }

  // Pass2: size × plan のマトリクスを構築
  const sizeMap = new Map();
  const planOrder = [];
  for (const e of entries) {
    if (!planOrder.includes(e.planName)) planOrder.push(e.planName);
    for (const row of e.rows) {
      const size = (row[0] || '').replace(/\*/g, '').trim();
      if (!isSizeCell(size)) continue;
      if (!sizeMap.has(size)) sizeMap.set(size, new Map());
      sizeMap.get(size).set(e.planName, normalizePrice(row[e.colIdx + 1]));
    }
  }

  const sizes = [...sizeMap.keys()].sort((a, b) => sizeNum(a) - sizeNum(b));
  const warnHeadings = [...new Set(
    entries.filter(e => DENY_RE.test(e.planName)).map(e => e.heading || '価格テーブル')
  )];

  return { sizes, planOrder, sizeMap, warnHeadings };
}

function toMarkdown(firm, wide) {
  const { sizes, planOrder, sizeMap, warnHeadings } = wide;
  const lines = [];
  lines.push(`<!-- source: data/price-collect/${firm}_price.md -->`);
  lines.push(`<!-- Page Maker: 取込エリアに貼付 → 「格納」ボタンで priceTable に格納 -->`);
  if (warnHeadings.length) {
    lines.push(`<!-- ⚠ 要確認: 以下のセクションは価格内訳（プロモ/定価/合計等）の列をプラン列として展開しています -->`);
    warnHeadings.forEach(w => lines.push(`<!-- - ${w} -->`));
  }
  lines.push('');
  lines.push(`| 口座サイズ | ${planOrder.join(' | ')} |`);
  lines.push(`|---|${planOrder.map(() => '---').join('|')}|`);
  for (const size of sizes) {
    const row = planOrder.map(p => sizeMap.get(size).get(p) ?? '—');
    lines.push(`| ${size} | ${row.join(' | ')} |`);
  }
  return lines.join('\n') + '\n';
}

mkdirSync(OUT_DIR, { recursive: true });
const files = readdirSync(SRC_DIR).filter(f => f.endsWith('_price.md'));
const summary = [];
for (const file of files) {
  const firm = file.replace(/_price\.md$/, '');
  const content = readFileSync(join(SRC_DIR, file), 'utf-8');
  const wide = buildWideTable(parseTables(content));
  if (!wide) { summary.push(`${firm}: ⚠ 価格テーブルが見つかりません`); continue; }
  writeFileSync(join(OUT_DIR, `${firm}_price.md`), toMarkdown(firm, wide), 'utf-8');
  const flag = wide.warnHeadings.length ? ' ⚠要確認' : '';
  summary.push(`${firm}: ${wide.sizes.length}サイズ × ${wide.planOrder.length}プラン${flag}`);
}
console.log(summary.join('\n'));
console.log(`\n出力先: ${OUT_DIR}`);
