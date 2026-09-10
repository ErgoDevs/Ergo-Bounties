// Ergo Bounty Radar — parser for ErgoDevs/Ergo-Bounties data/all.md
// Used both embedded in the page (live refresh) and standalone in node (tests).
function parseAllMd(text) {
  const rows = text.split('\n').filter(l => l.startsWith('| ['));
  const days = s => { const m = /^(\d+)d$/.exec(s); return m ? parseInt(m[1], 10) : null; };
  const out = [];
  for (const r of rows) {
    const cells = r.trim().replace(/^\|/, '').replace(/\|$/, '').split(' | ').map(c => c.trim());
    if (cells.length < 8) continue;
    const morg = /^\[([^\]]+)\]/.exec(cells[0]);
    const org = morg ? morg[1] : cells[0];
    const b = cells[1];
    const mrepo = /^\[([^\]]+)\]\((https:\/\/github\.com\/([^/)]+)\/([^/)]+))\)\/(.*)$/.exec(b);
    const repo = mrepo ? mrepo[4] : null;
    const rest = mrepo ? mrepo[5] : b;
    const mtitle = /^\[(.*)\]\((https:\/\/github\.com\/[^)]+)\)$/.exec(rest);
    let title, url;
    if (mtitle) { title = mtitle[1]; url = mtitle[2]; }
    else { title = rest; url = mrepo ? mrepo[2] : ''; }
    title = title.replace(/\\\[/g, '[').replace(/\\\]/g, ']');
    const v = cells[2];
    let erg = null, amount = null, currency = null;
    const mv = /~Σ([\d,]+(?:\.\d+)?)/.exec(v);
    if (mv) erg = parseFloat(mv[1].replace(/,/g, ''));
    const m2 = /^Σ([\d,]+(?:\.\d+)?)$/.exec(v);
    if (m2) { erg = parseFloat(m2[1].replace(/,/g, '')); amount = erg; currency = 'ERG'; }
    if (currency === null) {
      const m3 = /^([\d,]+(?:\.\d+)?)\s*(g\s+)?([A-Za-z]+)/.exec(v);
      if (m3) { amount = parseFloat(m3[1].replace(/,/g, '')); currency = (m3[2] ? 'g ' : '') + m3[3]; }
    }
    if (v.trim().toLowerCase() === 'ongoing') currency = 'Ongoing';
    if (v.trim() === 'Not specified') { currency = null; amount = null; }
    const age_days = days(cells[3]);
    const updated_days = days(cells[4]);
    const comments = /^\d+$/.test(cells[5]) ? parseInt(cells[5], 10) : null;
    const ml = /^\[([^\]]+)\]/.exec(cells[6]);
    const lang = ml ? ml[1] : cells[6];
    const mres = /\[!\[Reserve\][^\]]*\]\((https:\/\/github\.com\/ErgoDevs\/Ergo-Bounties\/new\/main\?[^)]+)\)/.exec(cells[7]);
    const reserve = mres ? mres[1] : null;
    let status = 'open';
    if (cells[7].includes('In%20Progress') || cells[7].includes('In Progress')) status = 'in-progress';
    if (currency === 'Ongoing') status = 'ongoing';
    let author = null;
    if (reserve) { const ma = /posted%20by%20([A-Za-z0-9_-]+)/.exec(reserve); if (ma) author = ma[1]; }
    out.push({
      org, repo, title, url, value_raw: v, amount, currency, erg,
      age_days, updated_days, comments, lang, reserve, status, author,
      stale: updated_days !== null && updated_days >= 180,
      // Raw convenience flag only. The app does NOT use this for its "high value"
      // badge: an ERG threshold silently redefines itself as the ERG price moves
      // (Σ1,000 was ~$237 in Aug 2026). See isHighValue() in index.html, which
      // thresholds in dollars and reads pegged amounts directly.
      high_value: erg !== null && erg >= 1000,
      starter: false, // filled from snapshot membership by URL
    });
  }
  return out;
}
if (typeof module !== 'undefined') module.exports = { parseAllMd };
