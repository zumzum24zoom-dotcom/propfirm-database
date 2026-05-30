/**
 * クーポン自動抽出スクリプト
 * GitHub Actions から月2回実行（毎月3日・18日）。
 * data/coupon-config.json のスキーマ: { firmSlug: { coupon: {...}, rules: {...} } }
 * type="coupon" のエントリを処理し data/firms/{slug}.json の「クーポン」を更新する。
 */

import { chromium } from 'playwright';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const ROOT       = join(dirname(fileURLToPath(import.meta.url)), '..');
const configPath = join(ROOT, 'data', 'coupon-config.json');
const firmsDir   = join(ROOT, 'data', 'firms');

const config = JSON.parse(readFileSync(configPath, 'utf-8'));
const today  = new Date().toISOString().split('T')[0];

const stats = { updated: 0, unchanged: 0, noCoupon: 0, broken: 0, error: 0 };

const browser = await chromium.launch({ headless: true });

for (const [slug, firmEntry] of Object.entries(config)) {
  if (slug.startsWith('_')) continue;

  // coupon エントリのみ処理（将来 rules 等が追加されても影響なし）
  const entry = firmEntry.coupon;
  if (!entry) continue;

  const firmPath = join(firmsDir, `${slug}.json`);
  if (!existsSync(firmPath)) {
    console.log(`⚠️  ${slug}: firm JSON が見つかりません`);
    continue;
  }

  const firmData = JSON.parse(readFileSync(firmPath, 'utf-8'));
  const page = await browser.newPage();

  try {
    await page.goto(entry.url, { waitUntil: 'networkidle', timeout: 30000 });

    const text = await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      return el ? (el.innerText || el.textContent || '').trim() : null;
    }, entry.selector);

    if (text === null) {
      console.log(`🔴 ${slug}: セレクター消失 — 再スキャンが必要`);
      entry.selectorBroken = true;
      entry.lastScanned = today;
      stats.broken++;
      continue;
    }

    delete entry.selectorBroken;
    const match = text.match(new RegExp(entry.pattern, 'i'));
    const code  = match ? match[1].toUpperCase() : null;

    const prevCoupons = JSON.stringify(firmData['クーポン'] || []);
    firmData['クーポン'] = code ? [{ code, updated: today }] : [];
    entry.lastScanned = today;
    if (code) entry.lastCode = code;

    const nextCoupons = JSON.stringify(firmData['クーポン']);
    if (prevCoupons !== nextCoupons) {
      writeFileSync(firmPath, JSON.stringify(firmData, null, 2));
      console.log(`✅ ${slug}: ${code ?? '(なし)'} → 更新`);
      stats.updated++;
    } else {
      console.log(`✔  ${slug}: ${code ?? '(なし)'} — 変更なし`);
      stats.unchanged++;
    }
    if (!code) stats.noCoupon++;

  } catch (e) {
    console.error(`❌ ${slug}: ${e.message}`);
    entry.lastScanned = today;
    stats.error++;
  } finally {
    await page.close();
  }
}

await browser.close();
writeFileSync(configPath, JSON.stringify(config, null, 2));

console.log(`\n━━━ 結果 ━━━\n更新: ${stats.updated} / 変更なし: ${stats.unchanged} / クーポンなし: ${stats.noCoupon} / 要再設定: ${stats.broken} / エラー: ${stats.error}`);
if (stats.broken > 0 || stats.error > 0) process.exit(1);
