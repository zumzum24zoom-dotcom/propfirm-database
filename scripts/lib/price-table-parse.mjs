/**
 * _work/price-collect/*_price.md と _work/price-collect/wide/*_price.md で共通の
 * マークダウンテーブル解析プリミティブ。convert-price-tables.mjs と
 * verify-price-tables.mjs で同一の解析セマンティクスを保証するために共有する。
 */

export const SIZE_HEADERS = new Set(['口座サイズ', '口座サイズ（USD）']);
export const NA_VALUES    = new Set(['', '-', 'ー', '―', 'N/A', 'n/a']);

export function parseRow(line) {
  const c = line.split('|').map(s => s.trim());
  if (c[0] === '') c.shift();
  if (c[c.length - 1] === '') c.pop();
  return c;
}

// マークダウンを「直前の見出し + テーブル」のリストに分解（先頭のファームタイトル見出しは除外）
export function parseTables(content) {
  const lines = content.split('\n').map(l => l.trim());
  const tables = [];
  let heading = null;
  let titleSkipped = false;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const h = line.match(/^#+\s*(.+)$/);
    if (h) {
      if (!titleSkipped) titleSkipped = true;
      else heading = h[1].trim();
      continue;
    }
    if (line.startsWith('|')) {
      const block = [];
      while (i < lines.length && lines[i].startsWith('|')) { block.push(lines[i]); i++; }
      i--;
      if (block.length >= 2) {
        tables.push({ heading, header: parseRow(block[0]), rows: block.slice(2).map(parseRow) });
      }
    }
  }
  return tables;
}

export function normalizePrice(v) {
  v = (v || '').trim();
  return NA_VALUES.has(v) ? '—' : v;
}

export function sizeNum(size) {
  const m = size.replace(/[,$€¥]/g, '').match(/[\d.]+/);
  return m ? parseFloat(m[0]) : Infinity;
}

// セルが「口座サイズ」行（区切り行・見出し行・非数値行ではない）かどうか
export function isSizeCell(cell) {
  if (!cell || /^[-:\s]+$/.test(cell)) return false;
  return /^[$¥€\d]/.test(cell);
}
