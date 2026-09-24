// One-off: rebuild radar/history/trends.json from this repo's own git history
// of data/all.md. Only needed to reseed the trend series from scratch; the
// daily workflow appends to it from then on.
//
//   node radar/scripts/backfill.js
//
// Needs full history, so in Actions check out with fetch-depth: 0.
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { parseAllMd } = require('./parser.js');
const REPO = process.env.LOCAL_DIR || path.join(__dirname, '..', '..');
const git = (cmd) => execSync(`git -C ${REPO} ${cmd}`, { encoding: 'utf8', maxBuffer: 64e6 });

function parseLegacy(text) {
  const out = [];
  for (const r of text.split('\n')) {
    if (!r.startsWith('| [')) continue;
    const cells = r.trim().replace(/^\|/, '').replace(/\|$/, '').split(' | ').map(c => c.trim());
    if (cells.length < 5 || cells.length >= 8) continue;
    const mtitle = /\]\((https:\/\/github\.com\/[^)]+\/(?:issues|discussions)\/\d+)\)/.exec(cells[1]);
    const url = mtitle ? mtitle[1] : null;
    let erg = null;
    const mv = /~Σ([\d,]+(?:\.\d+)?)/.exec(cells[2]) || /^Σ([\d,]+(?:\.\d+)?)$/.exec(cells[2]);
    if (mv) erg = parseFloat(mv[1].replace(/,/g, ''));
    out.push({ url, erg });
  }
  return out;
}

// build target dates: weekly since start, daily last 30 days
const targets = new Set();
const start = new Date('2025-03-23T00:00:00Z'), today = new Date('2026-08-10T00:00:00Z');
for (let d = new Date(start); d <= today; d = new Date(d.getTime() + 7 * 864e5)) targets.add(d.toISOString().slice(0, 10));
for (let d = new Date(today.getTime() - 30 * 864e5); d <= today; d = new Date(d.getTime() + 864e5)) targets.add(d.toISOString().slice(0, 10));

const seen = new Set(); const samples = [];
for (const t of [...targets].sort()) {
  let sha; try { sha = git(`rev-list -1 --before="${t} 23:59" HEAD -- data/all.md`).trim(); } catch (e) { continue; }
  if (!sha || seen.has(sha)) continue; seen.add(sha);
  const date = git(`log -1 --format=%ad --date=short ${sha}`).trim();
  let txt; try { txt = git(`show ${sha}:data/all.md`); } catch (e) { continue; }
  let rows = parseAllMd(txt);
  if (rows.length < 5) rows = parseLegacy(txt);
  if (rows.length < 20 || rows.length > 400) { console.error('skip', date, 'rows', rows.length); continue; }
  const erg = rows.reduce((a, b) => a + (b.erg || 0), 0);
  if (erg < 1000) { console.error('skip', date, 'erg', erg); continue; }
  let rate = null;
  try { const m = /SigUSD[^|]*\|\s*([\d.]+)/.exec(git(`show ${sha}:data/currency_prices.md`)); if (m) rate = parseFloat(m[1]); } catch (e) {}
  samples.push({ date, open: rows.length, erg: Math.round(erg), rate, usd: rate ? Math.round(erg / rate) : null, urls: new Set(rows.map(r => r.url).filter(Boolean)) });
}
samples.sort((a, b) => a.date < b.date ? -1 : 1);
// dedupe same-date (keep last), compute flows
const byDate = new Map(); for (const s of samples) byDate.set(s.date, s);
const seq = [...byDate.values()];
for (let i = 0; i < seq.length; i++) {
  const s = seq[i], p = i ? seq[i - 1] : null;
  s.added = p ? [...s.urls].filter(u => !p.urls.has(u)).length : null;
  s.removed = p ? [...p.urls].filter(u => !s.urls.has(u)).length : null;
}
for (const s of seq) delete s.urls;
fs.writeFileSync('/home/claude/repo/ergo-bounty-radar/history/trends.json', JSON.stringify({ samples: seq }));
console.log('samples:', seq.length, 'from', seq[0].date, 'to', seq[seq.length - 1].date);
console.log('first:', JSON.stringify(seq[0]), '\nmid:', JSON.stringify(seq[Math.floor(seq.length/2)]), '\nlast:', JSON.stringify(seq[seq.length - 1]));
const flows = seq.reduce((a, s) => ({ add: a.add + (s.added || 0), rem: a.rem + (s.removed || 0) }), { add: 0, rem: 0 });
console.log('total added/removed across period:', flows);
