#!/usr/bin/env node
// Web2MD連続ダンプ（複数ページが --- 区切りで連結された .md）を
// ページごとの個別ファイルに分割する。
//
// 使い方: node scripts/split-web2md-dump.mjs <input.md> <outDir> [--firm <slug>]
//   --firm を指定すると source URL のドメインが一致しないセクションは
//   "_excluded_<host>_*.md" として出力（誤混入の検知）
//
// Web2MD ダンプの各ページ形式:
//   # <title>
//   <空行>
//   *Source: [url](url)*
//   <空行>
//   ---
//   title: "..."
//   source: <url>
//   date: <iso>
//   ---
//   <body>
//
// 「# 見出し」直後に *Source: 行が続く場合のみページ境界として扱う。
// body内の単独 H1（# Prime opens. など）は無視。

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { basename, join } from 'node:path';

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node scripts/split-web2md-dump.mjs <input.md> <outDir> [--firm <slug>]');
  process.exit(1);
}
const [inputPath, outDir, ...rest] = args;
const firmIdx = rest.indexOf('--firm');
const firmSlug = firmIdx >= 0 ? rest[firmIdx + 1] : null;

mkdirSync(outDir, { recursive: true });
const raw = readFileSync(inputPath, 'utf8');
const lines = raw.split(/\r?\n/);

// ページ境界検出: 行 i が "# " で始まり、続く 1〜4 行以内に "*Source:" がある場合
function isPageBoundary(i) {
  if (!/^# [^#]/.test(lines[i])) return false;
  for (let j = 1; j <= 4 && i + j < lines.length; j++) {
    if (/^\*Source:/.test(lines[i + j])) return true;
    // 別の "# " or "---" が先に来たら境界ではない
    if (/^# /.test(lines[i + j])) return false;
  }
  return false;
}

// セクション区間を収集
const boundaries = [];
for (let i = 0; i < lines.length; i++) {
  if (isPageBoundary(i)) boundaries.push(i);
}
boundaries.push(lines.length);

const sections = [];
for (let k = 0; k < boundaries.length - 1; k++) {
  const start = boundaries[k];
  const end = boundaries[k + 1];
  const body = lines.slice(start, end);
  const title = body[0].replace(/^# /, '').trim();
  let sourceUrl = null;
  for (const line of body) {
    const m = line.match(/^source:\s*(\S+)/i);
    if (m) { sourceUrl = m[1]; break; }
  }
  sections.push({ title, sourceUrl, body });
}

const counts = { written: 0, excluded: 0, skipped: 0 };
const usedSlugs = new Set();

function urlToSlug(url) {
  if (!url) return 'unknown';
  try {
    const u = new URL(url);
    const path = u.pathname.replace(/\/$/, '').replace(/^\//, '');
    const last = path.split('/').pop() || u.hostname.replace(/\./g, '-');
    return last.toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80) || 'index';
  } catch {
    return 'unknown';
  }
}

function uniqueSlug(slug) {
  let s = slug;
  let n = 2;
  while (usedSlugs.has(s)) s = `${slug}-${n++}`;
  usedSlugs.add(s);
  return s;
}

for (const sec of sections) {
  if (!sec.sourceUrl) { counts.skipped++; continue; }
  const host = (() => { try { return new URL(sec.sourceUrl).hostname; } catch { return 'unknown'; } })();
  const isMatch = !firmSlug || host.includes(firmSlug.replace(/-/g, ''));
  const slug = uniqueSlug(urlToSlug(sec.sourceUrl));
  const prefix = isMatch ? '' : `_excluded_${host.replace(/\./g, '-')}__`;
  const outPath = join(outDir, `${prefix}${slug}.md`);
  writeFileSync(outPath, sec.body.join('\n'), 'utf8');
  if (isMatch) counts.written++; else counts.excluded++;
}

console.log(`split-web2md-dump: input=${basename(inputPath)}`);
console.log(`  sections found: ${sections.length}`);
console.log(`  written: ${counts.written}`);
console.log(`  excluded (firm mismatch): ${counts.excluded}`);
console.log(`  skipped (no source url): ${counts.skipped}`);
console.log(`  output dir: ${outDir}`);
