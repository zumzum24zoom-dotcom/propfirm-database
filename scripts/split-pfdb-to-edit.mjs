// pfdb.json（全社1ファイル）→ data/firms-edit/{slug}.json（1社1データ）へ分割。
// 「1社・1専用機・1データ」の土台。page-maker改 はこの1ファイルだけ読み書きする。
// slug は page-maker の slugify と完全一致させる（公開用 data/firms/{slug}.json と突合できるように）。
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const PFDB = join(ROOT, "data", "pfdb.json");
const OUT_DIR = join(ROOT, "data", "firms-edit");
const PUB_DIR = join(ROOT, "data", "firms");

// page-maker と同一実装（コピー）
const slugify = (str) => (str || "").toLowerCase()
  .replace(/\s+/g, "-").replace(/[^\w\-]/g, "").replace(/--+/g, "-").replace(/^-+|-+$/g, "");
const getSlotText = (sd, key) => {
  const arr = sd?.[key];
  if (!arr || arr.length === 0) return "";
  const m = arr.find(f => f.merged);
  return (m ? m.text : arr.map(f => f.text || "").join("\n")).trim();
};

const db = JSON.parse(readFileSync(PFDB, "utf-8"));
const tdm = db.tabDataMap || {};
mkdirSync(OUT_DIR, { recursive: true });

const pubSlugs = existsSync(PUB_DIR)
  ? new Set(readdirSync(PUB_DIR).filter(f => f.endsWith(".json") && !f.startsWith("_")).map(f => f.replace(/\.json$/, "")))
  : new Set();

const usedSlug = new Set();
let written = 0;
const noMatch = [];

for (const firm of db.firms || []) {
  const fd = tdm[firm.id] || {};
  const firmName = getSlotText(fd.slotData || {}, "firmName") || firm.name || "";
  let slug = slugify(firmName) || firm.id;
  // slug 重複は連番で一意化（同名ファーム対策）
  let s = slug, n = 2;
  while (usedSlug.has(s)) s = `${slug}-${n++}`;
  slug = s; usedSlug.add(slug);

  const tabData = {};
  if (tdm[firm.id]) tabData[firm.id] = tdm[firm.id];
  for (const plan of firm.plans || []) if (tdm[plan.id]) tabData[plan.id] = tdm[plan.id];

  const out = { schemaVersion: 1, slug, firm, tabData };
  writeFileSync(join(OUT_DIR, `${slug}.json`), JSON.stringify(out, null, 2) + "\n", "utf-8");
  written++;
  if (!pubSlugs.has(slug)) noMatch.push(slug);
}

console.log(`✔ ${written} firms → data/firms-edit/`);
console.log(`公開用(data/firms) と slug 不一致: ${noMatch.length ? noMatch.join(", ") : "なし"}`);
const onlyPub = [...pubSlugs].filter(s => !usedSlug.has(s));
console.log(`公開用にあるが pfdb に無い: ${onlyPub.length ? onlyPub.join(", ") : "なし"}`);
