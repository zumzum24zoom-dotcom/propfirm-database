/**
 * クーポン自動抽出スクリプト
 * GitHub Actions から月1回実行。
 * data/coupon-config.json のセレクター設定に従い各サイトを巡回し、
 * data/firms/{slug}.json の「クーポン」フィールドを更新する。
 *
 * 使用方法（ローカル）:
 *   node scripts/extract-coupons.mjs
 *
 * セレクターが壊れた（サイト改修）場合:
 *   coupon-config.json に "selectorBroken": true が付く
 *   → ブックマークレットで再スキャンしてセレクターを更新
 */

import { chromium } from 'playwright';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const configPath = join(ROOT, 'data', 'coupon-config.json');
const firmsDir  = join(ROOT, 'data', 'firms');

const config = JSON.parse(readFileSync(configPath, 'utf-8'));
const today  = new Date().toISOString().split('T')[0];

const stats = { updated: 0, unchanged: 0, noCoupon: 0, broken: 0, error: 0 };

const browser = await chromium.launch({ headless: true });

for (const [slug, entry] of Object.entries(config)) {
  if (slug.startsWith('_')) continue; // _note 等をスキップ

  const firmPath = join(firmsDir, `${slug}.json`);
  if (!existsSync(firmPath)) {
    console.log(`⚠️  ${slug}: firm JSON が見つかりません`);
    continue;
  }

  const firmData = JSON.parse(readFileSync(firmPath, 'utf-8'));
  const page = await browser.newPage();

  try {
    await page.goto(entry.url, { waitUntil: 'networkidle', timeout: 30000 });

    // セレクターで要素のテキストを取得
    const text = await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      return el ? (el.innerText || el.textContent || '').trim() : null;
    }, entry.selector);

    if (text === null) {
      // セレクターが見つからない = サイト改修の可能性
      console.log(`🔴 ${slug}: セレクター消失 — 再スキャンが必要`);
      entry.selectorBroken = true;
      entry.lastScanned = today;
      stats.broken++;
      continue;
    }

    // パターンマッチでコード抽出
    delete entry.selectorBroken; // 前回broken → 今回OK なら解除
    const match = text.match(new RegExp(entry.pattern, 'i'));
    const code  = match ? match[1].toUpperCase() : null;

    const prevCoupons = JSON.stringify(firmData['クーポン'] || []);

    if (code) {
      firmData['クーポン'] = [{ code, updated: today }];
      entry.lastCode    = code;
    } else {
      // 要素はあるがコード未検出 = クーポン終了
      firmData['クーポン'] = [];
    }

    entry.lastScanned = today;

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

// coupon-config.json を最終状態で保存（lastScanned / selectorBroken 等を更新）
writeFileSync(configPath, JSON.stringify(config, null, 2));

console.log(`
━━━ 結果 ━━━
更新     : ${stats.updated}
変更なし  : ${stats.unchanged}
クーポンなし: ${stats.noCoupon}
要再設定  : ${stats.broken}
エラー    : ${stats.error}
`);

// broken があれば終了コード1（GitHub Actionsで通知）
if (stats.broken > 0 || stats.error > 0) process.exit(1);
