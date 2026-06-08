import { useState, useMemo } from "react";

const C = {
  bg: "#0a0e17", surface: "#111827", border: "#1e2d3d",
  accent: "#00d4aa", yellow: "#f0b90b", red: "#ef4444", orange: "#f97316",
  text: "#c8d6e5", textBright: "#e2e8f0", textDim: "#636e7b",
  codeBg: "#0d1117", btnBg: "#1e2d3d",
  h1: "#00d4aa", h2: "#f0b90b", h3: "#7dd3fc", h4: "#a78bfa",
  tblHead: "#1a2744", tblAlt: "#0f1a2b",
};

/* ═══════════════════════════════════════════════════
   PREPROCESSOR — normalize messy Notion/Wraptas copy
   ═══════════════════════════════════════════════════ */

function preprocess(raw) {
  let t = raw;

  // 1) Split concatenated URLs
  t = t.replace(/\*\*([^*]+)\*\*(https?:\/\/)/g, "**$1**\n$2");
  for (let x = 0; x < 8; x++)
    t = t.replace(/(https?:\/\/[^\s]+?)(https?:\/\/)/g, "$1\n$2");

  const lines = t.split("\n");
  const out = [];

  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();

    // 2) Remove pure redundant separator rows: | --- | --- | ... |
    if (/^\|(\s*-+\s*\|)+\s*$/.test(trimmed)) continue;

    // 3) Split **Title**| table... into separate lines
    //    Pattern: **Something**| col1 | col2 | ... or **Something**(annotation)
    const titleTableMatch = trimmed.match(/^(\*\*[^*]+\*\*)\s*(\|.+)$/);
    if (titleTableMatch) {
      const title = titleTableMatch[1];
      const tablepart = titleTableMatch[2];
      out.push(title);
      // Now expand the concat table part
      const expanded = expandConcatPipe(tablepart);
      if (expanded) {
        out.push(...expanded);
      } else {
        out.push(tablepart);
      }
      continue;
    }

    // 4) Standalone concat pipe table (starts with |)
    if (trimmed.startsWith("|") && countPipes(trimmed) >= 10) {
      const expanded = expandConcatPipe(trimmed);
      if (expanded) {
        out.push(...expanded);
        continue;
      }
    }

    out.push(lines[i]);
  }

  return out.join("\n");
}

function countPipes(s) { let c = 0; for (const ch of s) if (ch === "|") c++; return c; }

function expandConcatPipe(line) {
  let s = line.trim();

  // Extract trailing annotation: ...| （※something）
  let trailingNote = "";
  const noteMatch = s.match(/^(.+\|)\s*(（※.+）.*)$/);
  if (noteMatch) {
    s = noteMatch[1];
    trailingNote = noteMatch[2];
  }

  // Strip leading/trailing pipe
  if (s.startsWith("|")) s = s.substring(1);
  if (s.endsWith("|")) s = s.substring(0, s.length - 1);

  const allCells = s.split("|").map(c => c.trim());

  // Build rows: empty cells are row boundaries
  const rows = [];
  let cur = [];
  for (let i = 0; i < allCells.length; i++) {
    if (allCells[i] === "" && cur.length > 0) {
      rows.push(cur);
      cur = [];
    } else if (allCells[i] !== "") {
      cur.push(allCells[i]);
    }
  }
  if (cur.length > 0) rows.push(cur);

  if (rows.length < 3) return null; // header + sep + data

  // Filter separator rows
  const dataRows = rows.filter(r => !r.every(c => /^:?-+:?$/.test(c)));
  if (dataRows.length < 2) return null;

  // Column count from majority of data rows
  const colCounts = dataRows.map(r => r.length);
  const mainCC = mode(colCounts);
  if (mainCC < 2) return null;

  // Check consistency
  const consistentRows = dataRows.filter(r => r.length === mainCC);
  if (consistentRows.length < 2) return null;

  // If first row has extra cell → title included; otherwise all same
  const firstRow = dataRows[0];
  const output = [];

  if (firstRow.length === mainCC) {
    // All rows have same col count → first row is headers
    output.push(`| ${firstRow.join(" | ")} |`);
  } else if (firstRow.length === mainCC + 1) {
    // First cell is title in bold, rest are headers
    // (title was already split out by preprocessor, but handle just in case)
    output.push(`| ${firstRow.slice(1).join(" | ")} |`);
  } else {
    return null;
  }

  output.push(`| ${Array(mainCC).fill("---").join(" | ")} |`);

  for (let r = 1; r < dataRows.length; r++) {
    const row = dataRows[r];
    if (row.length !== mainCC) continue; // skip inconsistent
    output.push(`| ${row.join(" | ")} |`);
  }

  if (trailingNote) {
    output.push("");
    output.push(trailingNote);
  }

  output.push("");
  return output;
}

function mode(arr) {
  const f = {};
  arr.forEach(v => f[v] = (f[v] || 0) + 1);
  let best = arr[0], bc = 0;
  for (const [k, v] of Object.entries(f)) if (v > bc) { best = Number(k); bc = v; }
  return best;
}

/* ═══════════════════════════════════════════════════
   STRUCTURING ENGINE
   ═══════════════════════════════════════════════════ */

function structureText(raw) {
  const processed = preprocess(raw);
  const lines = processed.split("\n");
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const trimmed = lines[i].trim();

    if (trimmed === "") { blocks.push({ type: "blank" }); i++; continue; }

    // Markdown heading: ## Text or ##Text
    const mdH = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (mdH) {
      blocks.push({ type: "heading", level: mdH[1].length, text: cleanHeading(mdH[2]) });
      i++; continue;
    }

    // Escaped numbered heading: 1\. Title (Notion export)
    const escNum = trimmed.match(/^(\d+)\\[.．]\s+(.+)$/);
    if (escNum) {
      blocks.push({ type: "heading", level: 3, text: `${escNum[1]}. ${cleanHeading(escNum[2])}` });
      i++; continue;
    }

    // Bare numbered heading without escape: "1. Title" where short + no period ending
    // (only if not a list item — check: is it short and followed by body text?)
    const bareNum = trimmed.match(/^(\d+)\.\s+(.+)$/);
    if (bareNum && trimmed.length < 60 && !trimmed.endsWith("。") && !trimmed.endsWith("、")) {
      const next = (lines[i + 1] || "").trim();
      if (next === "" || next.startsWith("-") || next.startsWith("・") || /^[A-Z]/.test(next) || next.length > 40) {
        blocks.push({ type: "heading", level: 3, text: `${bareNum[1]}. ${cleanHeading(bareNum[2])}` });
        i++; continue;
      }
    }

    // Underline headings
    if (i + 1 < lines.length && /^={3,}$/.test((lines[i + 1] || "").trim()) && trimmed.length > 0) {
      blocks.push({ type: "heading", level: 1, text: trimmed }); i += 2; continue;
    }
    if (i + 1 < lines.length && /^-{3,}$/.test((lines[i + 1] || "").trim()) && trimmed.length > 0 && !/^[-|]/.test(trimmed)) {
      blocks.push({ type: "heading", level: 2, text: trimmed }); i += 2; continue;
    }

    // HR
    if (/^\\?[-=*─━]{3,}$/.test(trimmed)) { blocks.push({ type: "hr" }); i++; continue; }

    // Bold standalone → sub-heading
    const boldLine = trimmed.match(/^\*\*(.+)\*\*$/);
    if (boldLine) {
      const lastH = [...blocks].reverse().find(b => b.type === "heading");
      const level = lastH ? Math.min(lastH.level + 1, 5) : 3;
      blocks.push({ type: "heading", level, text: boldLine[1] });
      i++; continue;
    }

    // 【brackets】
    if (/^【.+】$/.test(trimmed) || /^［.+］$/.test(trimmed)) {
      blocks.push({ type: "heading", level: 2, text: trimmed.replace(/^[【［]|[】］]$/g, "") });
      i++; continue;
    }

    // Note: （※...）
    if (/^（※.+）/.test(trimmed)) {
      blocks.push({ type: "note", text: trimmed });
      i++; continue;
    }

    // ── PIPE TABLE ──
    if (trimmed.startsWith("|") && trimmed.split("|").length >= 3) {
      const tl = [];
      let j = i;
      while (j < lines.length) {
        const lt = lines[j].trim();
        if (lt.startsWith("|") && lt.split("|").length >= 3) { tl.push(lt); j++; }
        else break;
      }
      const parsed = parsePipeTable(tl);
      if (parsed) { blocks.push({ type: "table", ...parsed }); i = j; continue; }
    }

    // ── TAB TABLE ──
    if (trimmed.includes("\t") && trimmed.split("\t").length >= 2) {
      const tl = [];
      let j = i;
      while (j < lines.length && lines[j].trim().includes("\t") && lines[j].trim().split("\t").length >= 2) {
        tl.push(lines[j].trim()); j++;
      }
      if (tl.length >= 2) {
        const p = parseTabTable(tl);
        if (p) { blocks.push({ type: "table", ...p }); i = j; continue; }
      }
    }

    // ── KV TABLE ──
    const kvM = trimmed.match(/^(.{1,40})\s*[:：]\s*(.+)$/);
    if (kvM && !/^https?:/.test(trimmed)) {
      const pairs = [];
      let j = i;
      while (j < lines.length) {
        const lt = lines[j].trim();
        if (lt === "") break;
        const m = lt.match(/^(.{1,40})\s*[:：]\s*(.+)$/);
        if (m && !/^https?:/.test(lt)) { pairs.push([m[1].trim(), m[2].trim()]); j++; }
        else break;
      }
      if (pairs.length >= 3) {
        blocks.push({ type: "table", headers: ["項目", "内容"], rows: pairs });
        i = j; continue;
      }
    }

    // ── BULLET LIST ──
    const bulletRe = /^([-・●▶▸★☆◆◇■□→►•])\s+(.+)$/;
    if (bulletRe.test(trimmed)) {
      const items = [];
      while (i < lines.length) {
        const lt = lines[i]?.trim() || "";
        if (lt === "") break;
        const m = lt.match(bulletRe);
        if (m) {
          const indent = (lines[i].match(/^(\s*)/)[1] || "").length >= 2 ? 1 : 0;
          items.push({ text: m[2], indent }); i++;
        } else if ((lines[i].match(/^(\s*)/)[1] || "").length >= 4 && lt) {
          if (items.length) items[items.length - 1].text += " " + lt; i++;
        } else break;
      }
      blocks.push({ type: "list", ordered: false, items }); continue;
    }

    // ── ORDERED LIST (long items, not headings) ──
    const olRe = /^(\d+)[.．)\）]\s+(.+)$/;
    if (olRe.test(trimmed) && (trimmed.length >= 60 || trimmed.endsWith("。"))) {
      const items = [];
      while (i < lines.length) {
        const lt = lines[i]?.trim() || "";
        if (lt === "") break;
        const m = lt.match(olRe);
        if (m) { items.push({ text: m[2], indent: 0 }); i++; }
        else break;
      }
      blocks.push({ type: "list", ordered: true, items }); continue;
    }

    // ── URLS ──
    if (/^https?:\/\//.test(trimmed)) {
      const urls = [];
      while (i < lines.length && /^https?:\/\//.test(lines[i]?.trim() || "")) {
        urls.push(lines[i].trim()); i++;
      }
      blocks.push({ type: "links", urls }); continue;
    }

    // ── SHORT STANDALONE → heading heuristic ──
    if (trimmed.length <= 50 && !trimmed.endsWith("。") && !trimmed.endsWith("、") && !trimmed.endsWith(".")) {
      const next = (lines[i + 1] || "").trim();
      if (next === "" || /^[-・●▶▸★☆◆◇■□→►•\d|*]/.test(next)) {
        const lastH = [...blocks].reverse().find(b => b.type === "heading");
        const level = !lastH ? 2 : Math.min(lastH.level + 1, 5);
        blocks.push({ type: "heading", level, text: trimmed }); i++; continue;
      }
    }

    // ── PARAGRAPH ──
    const pl = [trimmed]; i++;
    while (i < lines.length) {
      const nt = lines[i].trim();
      if (nt === "") break;
      if (/^(#{1,6}\s|\d+\\?[.．]\s|[-・●▶▸★☆◆◇■□→►•]\s|【|\*\*|\\?[-=*─]{3,}$|（※)/.test(nt)) break;
      if (nt.startsWith("|") && nt.split("|").length >= 3) break;
      if (/^https?:\/\//.test(nt)) break;
      pl.push(nt); i++;
    }
    blocks.push({ type: "paragraph", text: pl.join("\n") });
  }

  return blocks;
}

function cleanHeading(t) { return t.replace(/\\([.#])/g, "$1").replace(/\*\*/g, "").trim(); }

function parsePipeTable(lines) {
  const parse = l => l.replace(/^\|/, "").replace(/\|$/, "").split("|").map(c => c.trim());
  const filtered = lines.filter(l => !/^\|\s*[-:]+\s*(\|\s*[-:]+\s*)*\|?\s*$/.test(l));
  if (filtered.length < 2) return null;
  const headers = parse(filtered[0]);
  if (headers.length < 2) return null;
  const rows = filtered.slice(1).map(r => {
    const cells = parse(r);
    while (cells.length < headers.length) cells.push("");
    return cells.slice(0, headers.length);
  });
  if (rows.length < 1) return null;
  return { headers, rows };
}

function parseTabTable(lines) {
  const rows = lines.map(l => l.split("\t").map(c => c.trim()));
  return { headers: rows[0], rows: rows.slice(1) };
}

/* ═══════════════════════════════════════════════════
   OUTPUT
   ═══════════════════════════════════════════════════ */

function toMarkdown(blocks) {
  return blocks.map(b => {
    if (b.type === "blank") return "";
    if (b.type === "hr") return "---";
    if (b.type === "heading") return `${"#".repeat(b.level)} ${b.text}`;
    if (b.type === "paragraph") return b.text;
    if (b.type === "note") return `> ${b.text}`;
    if (b.type === "list")
      return b.items.map((it, idx) => `${"  ".repeat(it.indent)}${b.ordered ? `${idx+1}.` : "-"} ${it.text}`).join("\n");
    if (b.type === "table") {
      const h = `| ${b.headers.join(" | ")} |`;
      const s = `| ${b.headers.map(() => "---").join(" | ")} |`;
      const r = b.rows.map(row => `| ${row.join(" | ")} |`).join("\n");
      return `${h}\n${s}\n${r}`;
    }
    if (b.type === "links") return b.urls.map(u => `- ${u}`).join("\n");
    return "";
  }).join("\n\n").replace(/\n{3,}/g, "\n\n").trim();
}

function toHTML(blocks) {
  return blocks.map(b => {
    if (b.type === "blank") return "";
    if (b.type === "hr") return "<hr>";
    if (b.type === "heading") return `<h${b.level}>${esc(b.text)}</h${b.level}>`;
    if (b.type === "paragraph") return `<p>${esc(b.text)}</p>`;
    if (b.type === "note") return `<blockquote><p>${esc(b.text)}</p></blockquote>`;
    if (b.type === "list") {
      const tag = b.ordered ? "ol" : "ul";
      return `<${tag}>\n${b.items.map(it => `  <li>${esc(it.text)}</li>`).join("\n")}\n</${tag}>`;
    }
    if (b.type === "table") {
      const hdr = b.headers.map(h => `<th>${esc(h)}</th>`).join("");
      const rows = b.rows.map(r => `  <tr>${r.map(c => `<td>${esc(c)}</td>`).join("")}</tr>`).join("\n");
      return `<table>\n  <thead><tr>${hdr}</tr></thead>\n  <tbody>\n${rows}\n  </tbody>\n</table>`;
    }
    if (b.type === "links")
      return `<ul class="refs">\n${b.urls.map(u => `  <li><a href="${esc(u)}">${esc(u)}</a></li>`).join("\n")}\n</ul>`;
    return "";
  }).filter(Boolean).join("\n").trim();
}

function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

/* ═══════════════════════════════════════════════════
   UI
   ═══════════════════════════════════════════════════ */

function copyToClipboard(t) {
  if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(t).catch(() => fbC(t));
  return fbC(t);
}
function fbC(t) {
  return new Promise(r => {
    const a = document.createElement("textarea"); a.value = t; a.style.cssText = "position:fixed;left:-9999px";
    document.body.appendChild(a); a.select(); try { document.execCommand("copy"); } catch {} document.body.removeChild(a); r();
  });
}

function CBtn({ text, label }) {
  const [ok, setOk] = useState(false);
  if (!text) return null;
  return <button onClick={() => copyToClipboard(text).then(() => { setOk(true); setTimeout(() => setOk(false), 1500); })}
    style={{ background: ok ? C.accent : C.btnBg, color: ok ? C.bg : C.accent, border: `1px solid ${ok ? C.accent : C.border}`, padding: "7px 18px", borderRadius: 6, cursor: "pointer", fontSize: "0.82rem", fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}
  >{ok ? "✓ Copied" : label || "Copy"}</button>;
}

function Pv({ block: b }) {
  const hC = { 1: C.h1, 2: C.h2, 3: C.h3, 4: C.h4, 5: C.textBright };
  const hS = { 1: "1.35rem", 2: "1.1rem", 3: "0.95rem", 4: "0.88rem", 5: "0.84rem" };

  if (b.type === "blank") return <div style={{ height: 6 }} />;
  if (b.type === "hr") return <hr style={{ border: "none", borderTop: `1px solid ${C.border}`, margin: "12px 0" }} />;
  if (b.type === "heading") return (
    <div style={{ fontSize: hS[b.level] || "0.84rem", fontWeight: 700, color: hC[b.level] || C.textBright, margin: "14px 0 6px", borderBottom: b.level <= 2 ? `1px solid ${C.border}` : "none", paddingBottom: b.level <= 2 ? 4 : 0 }}>
      <span style={{ color: C.textDim, fontSize: "0.6rem", marginRight: 6, fontFamily: "'JetBrains Mono', monospace" }}>H{b.level}</span>{b.text}
    </div>
  );
  if (b.type === "paragraph") return <p style={{ fontSize: "0.84rem", color: C.text, lineHeight: 1.7, margin: "6px 0", whiteSpace: "pre-wrap" }}>{b.text}</p>;
  if (b.type === "note") return <div style={{ fontSize: "0.78rem", color: C.textDim, borderLeft: `3px solid ${C.yellow}`, paddingLeft: 12, margin: "8px 0", fontStyle: "italic" }}>{b.text}</div>;
  if (b.type === "list") return (
    <ul style={{ margin: "6px 0", paddingLeft: 22, fontSize: "0.84rem", color: C.text, lineHeight: 1.7, listStyleType: b.ordered ? "decimal" : "disc" }}>
      {b.items.map((it, i) => <li key={i} style={{ marginLeft: it.indent * 18, marginBottom: 2 }}>{it.text}</li>)}
    </ul>
  );
  if (b.type === "table") return (
    <div style={{ overflowX: "auto", margin: "10px 0" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.76rem", fontFamily: "'JetBrains Mono', monospace" }}>
        <thead><tr>{b.headers.map((h, ci) => (
          <th key={ci} style={{ background: C.tblHead, color: C.yellow, padding: "8px 10px", textAlign: "left", borderBottom: `2px solid ${C.accent}`, fontWeight: 700, whiteSpace: "nowrap" }}>{h}</th>
        ))}</tr></thead>
        <tbody>{b.rows.map((row, ri) => (
          <tr key={ri}>{row.map((cell, ci) => (
            <td key={ci} style={{ background: ri % 2 === 0 ? "transparent" : C.tblAlt, color: C.text, padding: "6px 10px", borderBottom: `1px solid ${C.border}` }}>{cell}</td>
          ))}</tr>
        ))}</tbody>
      </table>
    </div>
  );
  if (b.type === "links") return (
    <div style={{ fontSize: "0.7rem", color: C.textDim, margin: "8px 0", fontFamily: "'JetBrains Mono', monospace" }}>
      {b.urls.map((u, i) => <div key={i} style={{ marginBottom: 2, wordBreak: "break-all" }}>{u}</div>)}
    </div>
  );
  return null;
}

function getStats(blocks) {
  let h=0, p=0, li=0, liI=0, tbl=0, tblR=0;
  blocks.forEach(b => {
    if (b.type==="heading") h++; if (b.type==="paragraph") p++;
    if (b.type==="list") { li++; liI+=b.items.length; }
    if (b.type==="table") { tbl++; tblR+=b.rows.length; }
  });
  return { h, p, li, liI, tbl, tblR };
}

export default function App() {
  const [input, setInput] = useState("");
  const [fmt, setFmt] = useState("markdown");
  const [pv, setPv] = useState(true);

  const blocks = useMemo(() => input.trim() ? structureText(input) : [], [input]);
  const output = useMemo(() => blocks.length ? (fmt==="markdown" ? toMarkdown(blocks) : toHTML(blocks)) : "", [blocks, fmt]);
  const st = useMemo(() => getStats(blocks), [blocks]);

  return (
    <div style={{ fontFamily: "'Noto Sans JP', sans-serif", background: C.bg, color: C.text, minHeight: "100vh", padding: "16px 20px", maxWidth: 1200, margin: "0 auto" }}>
      <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet" />

      <div style={{ marginBottom: 16 }}>
        <h1 style={{ fontSize: "1.3rem", color: C.accent, fontWeight: 700, margin: "0 0 4px", fontFamily: "'JetBrains Mono', monospace" }}>✦ Text Structurer</h1>
        <p style={{ fontSize: "0.76rem", color: C.textDim, margin: 0 }}>Notion/Wraptas連結テーブル・エスケープ見出し対応 → Markdown / HTML</p>
      </div>

      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
        <div style={{ display: "flex", border: `1px solid ${C.border}`, borderRadius: 6, overflow: "hidden" }}>
          {["markdown","html"].map(f => (
            <button key={f} onClick={() => setFmt(f)} style={{
              background: fmt===f ? C.accent : C.btnBg, color: fmt===f ? C.bg : C.text,
              border: "none", padding: "6px 18px", cursor: "pointer", fontWeight: 700,
              fontSize: "0.82rem", fontFamily: "'JetBrains Mono', monospace",
            }}>{f==="markdown" ? "Markdown" : "HTML"}</button>
          ))}
        </div>
        <button onClick={() => setPv(!pv)} style={{
          background: pv ? C.yellow : C.btnBg, color: pv ? C.bg : C.textDim,
          border: `1px solid ${pv ? C.yellow : C.border}`, padding: "6px 14px",
          borderRadius: 6, cursor: "pointer", fontWeight: 600, fontSize: "0.8rem",
        }}>{pv ? "Preview ON" : "Preview OFF"}</button>
        <button onClick={() => setInput("")} style={{
          background: C.btnBg, color: C.red, border: `1px solid ${C.border}`,
          padding: "6px 14px", borderRadius: 6, cursor: "pointer", fontSize: "0.78rem",
        }}>クリア</button>
        {blocks.length > 0 && (
          <div style={{ marginLeft: "auto", display: "flex", gap: 12, fontSize: "0.72rem", fontFamily: "'JetBrains Mono', monospace", color: C.textDim }}>
            {st.h>0 && <span>H:<b style={{color:C.h2}}>{st.h}</b></span>}
            {st.p>0 && <span>P:<b style={{color:C.text}}>{st.p}</b></span>}
            {st.li>0 && <span>List:<b style={{color:C.accent}}>{st.li}</b>({st.liI})</span>}
            {st.tbl>0 && <span>Tbl:<b style={{color:C.orange}}>{st.tbl}</b>({st.tblR}r)</span>}
          </div>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: blocks.length > 0 ? "1fr 1fr" : "1fr", gap: 16, marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: "0.72rem", color: C.textDim, marginBottom: 4, fontFamily: "'JetBrains Mono', monospace" }}>INPUT</div>
          <textarea value={input} onChange={e => setInput(e.target.value)}
            placeholder={"Notion/Wraptasからコピペしたテキストを貼り付け...\n\n連結パイプテーブル / **Title**|table|\nN\\. エスケープ見出し / ### 見出し\n- リスト / （※注釈）/ URL"}
            style={{ width: "100%", minHeight: 420, background: C.codeBg, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14, color: C.textBright, fontSize: "0.84rem", fontFamily: "'JetBrains Mono', monospace", lineHeight: 1.7, resize: "vertical", outline: "none", boxSizing: "border-box" }}
          />
        </div>
        {blocks.length > 0 && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
              <span style={{ fontSize: "0.72rem", color: C.textDim, fontFamily: "'JetBrains Mono', monospace" }}>OUTPUT — {fmt==="markdown" ? "Markdown" : "HTML"}</span>
              <CBtn text={output} label="Copy" />
            </div>
            <pre style={{ width: "100%", minHeight: 420, maxHeight: 600, overflowY: "auto", background: C.codeBg, border: `1px solid ${C.border}`, borderRadius: 8, padding: 14, color: C.textBright, fontSize: "0.76rem", fontFamily: "'JetBrains Mono', monospace", lineHeight: 1.7, margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word", boxSizing: "border-box" }}>{output}</pre>
          </div>
        )}
      </div>

      {pv && blocks.length > 0 && (
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, borderBottom: `1px solid ${C.border}`, paddingBottom: 8 }}>
            <span style={{ fontSize: "0.85rem", color: C.accent, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>▸ Preview</span>
            <span style={{ fontSize: "0.7rem", color: C.textDim, fontFamily: "'JetBrains Mono', monospace" }}>{blocks.filter(b=>b.type!=="blank").length} blocks</span>
          </div>
          {blocks.map((b, i) => <Pv key={i} block={b} />)}
        </div>
      )}
    </div>
  );
}
