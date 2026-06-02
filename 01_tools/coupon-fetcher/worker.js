/**
 * pfd-coupon-fetcher
 * 毎月1日 00:00 UTC に全Firmの公式サイトを巡回し、クーポンコードを自動取得。
 * data/firms/*.json の「クーポン」フィールドを更新して GitHub にバッチコミットする。
 *
 * 必要な環境変数 (Cloudflare Secrets):
 *   ANTHROPIC_KEY   — Anthropic APIキー
 *   GITHUB_TOKEN    — repo書き込み権限のある Personal Access Token
 *   TRIGGER_SECRET  — 手動トリガー用パスフレーズ（任意の文字列）
 *
 * wrangler.toml の [vars] で設定:
 *   GITHUB_REPO    = "zumzum24zoom-dotcom/propfirm-database"
 *   GITHUB_BRANCH  = "master"
 */

const MODEL = "claude-haiku-4-5-20251001";
const FIRMS_DIR = "data/firms";
const HTML_LIMIT = 8000; // 先頭8KBをClaudeに渡す

export default {
  // cron トリガー: wrangler.toml の crons = ["0 0 1 * *"]
  async scheduled(event, env, ctx) {
    ctx.waitUntil(run(env));
  },

  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    if (url.searchParams.get("secret") !== env.TRIGGER_SECRET) {
      return cors(json({ error: "unauthorized" }, 401));
    }

    // POST /scan — ブックマークレット / Page Maker からのページ構造保存
    if (request.method === "POST" && url.pathname === "/scan") {
      const body = await request.json();
      const { firmSlug, data } = body;
      if (!firmSlug) return cors(json({ error: "firmSlug required" }, 400));
      const [owner, repo] = env.GITHUB_REPO.split("/");
      await ghPutFile(owner, repo, env.GITHUB_BRANCH || "master",
        `data/scans/${firmSlug}.json`,
        JSON.stringify(data, null, 2),
        env.GITHUB_TOKEN
      );
      return cors(json({ status: "saved", path: `data/scans/${firmSlug}.json` }));
    }

    // GET /?secret=... — 手動クーポン取得トリガー
    ctx.waitUntil(run(env));
    return cors(json({ status: "started", message: "バックグラウンドで実行中" }, 202));
  }
};

// ── メイン処理 ──────────────────────────────────────────────────────────

async function run(env) {
  const [owner, repo] = env.GITHUB_REPO.split("/");
  const branch = env.GITHUB_BRANCH || "master";

  console.log(`[coupon-fetcher] 開始 ${new Date().toISOString()}`);

  // 1. data/firms/ 配下の *.json を一覧取得
  const dirEntries = await ghList(owner, repo, FIRMS_DIR, env.GITHUB_TOKEN);
  const firmFiles = dirEntries.filter(e => e.type === "file" && e.name.endsWith(".json"));
  console.log(`[coupon-fetcher] ${firmFiles.length} 件のFirmファイルを検出`);

  const updates = []; // { path, content }

  for (const file of firmFiles) {
    try {
      const { content: rawJson, sha } = await ghGetFile(owner, repo, file.path, env.GITHUB_TOKEN);
      const firm = JSON.parse(rawJson);

      const targetUrl = (firm["アフィリエイトURL"] || firm["公式URL"] || "").trim();
      if (!targetUrl) {
        console.log(`[skip] ${file.name}: URL未設定`);
        continue;
      }

      // 2. 公式サイトのHTMLを取得
      let html = "";
      try {
        const resp = await fetch(targetUrl, {
          headers: { "User-Agent": "Mozilla/5.0 (compatible; PFD-CouponBot/1.0)" },
          redirect: "follow",
          signal: AbortSignal.timeout(10000)
        });
        html = (await resp.text()).slice(0, HTML_LIMIT);
      } catch (fetchErr) {
        console.log(`[skip] ${file.name}: fetch失敗 — ${fetchErr.message}`);
        continue;
      }

      // 3. Claude Haiku でクーポンコードを抽出
      const coupons = await extractCoupons(
        firm["ファーム名"] || file.name.replace(".json", ""),
        targetUrl,
        html,
        env.ANTHROPIC_KEY
      );
      console.log(`[result] ${file.name}: ${coupons.length} 件`);

      // 4. 変更がある場合のみ更新対象に追加
      if (JSON.stringify(firm["クーポン"] || []) !== JSON.stringify(coupons)) {
        firm["クーポン"] = coupons;
        updates.push({ path: file.path, content: JSON.stringify(firm, null, 2) });
      }

      // API レート制限対策
      await sleep(1200);
    } catch (err) {
      console.error(`[error] ${file.name}: ${err.message}`);
    }
  }

  if (!updates.length) {
    console.log("[coupon-fetcher] 変更なし — コミットをスキップ");
    return;
  }

  // 5. GitHub にバッチコミット（1コミットで全ファイル更新）
  await batchCommit(owner, repo, branch, updates, env.GITHUB_TOKEN);
  console.log(`[coupon-fetcher] 完了 — ${updates.length} ファイル更新`);
}

// ── クーポン抽出 ─────────────────────────────────────────────────────────

async function extractCoupons(firmName, url, html, apiKey) {
  const prompt = `プロップファームの公式サイトHTMLからクーポン・プロモーションコードを抽出してください。

ファーム: ${firmName}
URL: ${url}

抽出ルール:
- コード形式（英数字/ハイフン/アンダースコア）のプロモコードのみ
- 割引率・割引額の説明も含める
- 期限情報があれば含める（YYYY-MM-DD形式、不明はnull）
- 見つからない場合は空配列 []

出力: JSONのみ（説明不要）
形式: [{"code":"SAVE10","discount":"10%割引","expires":"2026-06-30"}]

HTML:
${html}`;

  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json"
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 512,
      messages: [{ role: "user", content: prompt }]
    })
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(`Claude API ${resp.status}: ${err.error?.message || "unknown"}`);
  }

  const data = await resp.json();
  const text = data.content[0].text.trim().replace(/```json|```/g, "").trim();
  try {
    const parsed = JSON.parse(text);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

// ── GitHub API helpers ────────────────────────────────────────────────────

async function ghList(owner, repo, path, token) {
  const resp = await ghFetch(
    `https://api.github.com/repos/${owner}/${repo}/contents/${path}`, token
  );
  if (!resp.ok) return [];
  return resp.json();
}

async function ghGetFile(owner, repo, path, token) {
  const resp = await ghFetch(
    `https://api.github.com/repos/${owner}/${repo}/contents/${path}`, token
  );
  if (!resp.ok) throw new Error(`GitHub: ${path} が取得できません (${resp.status})`);
  const data = await resp.json();
  return {
    sha: data.sha,
    content: decodeURIComponent(escape(atob(data.content.replace(/\s/g, ""))))
  };
}

function ghFetch(url, token, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      Authorization: `token ${token}`,
      "User-Agent": "pfd-coupon-fetcher",
      Accept: "application/vnd.github.v3+json",
      ...(options.headers || {})
    }
  });
}

async function ghPutFile(owner, repo, branch, path, content, token) {
  const base = `https://api.github.com/repos/${owner}/${repo}`;
  const existing = await ghFetch(`${base}/contents/${path}`, token);
  const sha = existing.ok ? (await existing.json()).sha : undefined;
  await ghFetch(`${base}/contents/${path}`, token, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: `[scan] ${path}`,
      content: btoa(unescape(encodeURIComponent(content))),
      branch,
      ...(sha ? { sha } : {})
    })
  });
}

async function batchCommit(owner, repo, branch, updates, token) {
  const base = `https://api.github.com/repos/${owner}/${repo}`;

  // ① 現在のブランチ先頭SHAを取得
  const refData = await ghFetch(`${base}/git/refs/heads/${branch}`, token).then(r => r.json());
  const latestSha = refData.object.sha;

  // ② base tree SHA を取得
  const commitData = await ghFetch(`${base}/git/commits/${latestSha}`, token).then(r => r.json());
  const baseTreeSha = commitData.tree.sha;

  // ③ 各ファイルの blob を作成
  const treeItems = [];
  for (const { path, content } of updates) {
    const blob = await ghFetch(`${base}/git/blobs`, token, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, encoding: "utf-8" })
    }).then(r => r.json());
    treeItems.push({ path, mode: "100644", type: "blob", sha: blob.sha });
  }

  // ④ 新しい tree を作成
  const tree = await ghFetch(`${base}/git/trees`, token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ base_tree: baseTreeSha, tree: treeItems })
  }).then(r => r.json());

  // ⑤ コミット作成
  const today = new Date().toISOString().split("T")[0];
  const newCommit = await ghFetch(`${base}/git/commits`, token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: `[auto] クーポン更新 ${today}`,
      tree: tree.sha,
      parents: [latestSha]
    })
  }).then(r => r.json());

  // ⑥ ブランチを前進
  await ghFetch(`${base}/git/refs/heads/${branch}`, token, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sha: newCommit.sha })
  });
}

// ── utils ─────────────────────────────────────────────────────────────────

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
  };
}

function cors(response) {
  const r = new Response(response.body, response);
  Object.entries(corsHeaders()).forEach(([k, v]) => r.headers.set(k, v));
  return r;
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}
