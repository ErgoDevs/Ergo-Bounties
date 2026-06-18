<div align="center">
  <h1>🏆 Ergo Ecosystem Bounties</h1>
  <p><em>The Central Hub for Discovering, Claiming, and Managing Ergo Bounties</em></p>
  <p>
    <a href="/data/all.md"><img src="https://img.shields.io/badge/Open%20Bounties-107%2B-4CAF50" alt="Open Bounties"></a>
    <a href="/data/summary.md"><img src="https://img.shields.io/badge/💰%20Total%20Value-130,531.50%20ERG-2196F3" alt="Total Value"></a>
    <a href="/data/high-value-bounties.md"><img src="https://img.shields.io/badge/🌟%20High%20Value-38%2B%20Over%201000%20ERG-FFC107" alt="High Value Bounties"></a>
    <a href="/docs/ongoing-programs.md"><img src="https://img.shields.io/badge/🔥%20Grants%20and%20Initiatives-9C27B0" alt="Featured Bounties"></a>
  </p>
  <h2>🚀 Get Started</h2>
  <p><em>Find, claim, and contribute to Ergo ecosystem bounties across 100+ indexed repositories</em></p>
  <p>
    <a href="/data/all.md"><img src="https://img.shields.io/badge/✅%20Browse%20Bounties-3F51B5" alt="Browse Bounties"></a>
    <a href="/docs/bounty-submission-guide.md#reserving-a-bounty"><img src="https://img.shields.io/badge/🔒%20Reserve%20a%20Bounty-green" alt="Reserve a Bounty"></a>
    <a href="/docs/bounty-submission-guide.md#step-by-step-submission-process"><img src="https://img.shields.io/badge/💰%20Request%20Payment-orange" alt="Request Payment"></a>
    <a href="/docs/add-missing-bounty-guide.md"><img src="https://img.shields.io/badge/➕%20Add%20Bounty-red" alt="Add a New Bounty"></a>
  </p>
  <h2>📚 Explore Bounties by Category</h2>
  <div>
    <h3>🔤 By Programming Language</h3>
    <p>
          <a href="/data/by_language/scala.md"><img src="https://img.shields.io/badge/Scala-76-DC322F"></a>
    <a href="/data/by_language/rust.md"><img src="https://img.shields.io/badge/Rust-14-DEA584"></a>
    <a href="/data/by_language/typescript.md"><img src="https://img.shields.io/badge/TypeScript-7-3178C6"></a>
    <a href="/data/by_language/svelte.md"><img src="https://img.shields.io/badge/Svelte-2-DC322F"></a>
    <a href="/data/by_language/various.md"><img src="https://img.shields.io/badge/Various-3-DC322F"></a>
    <a href="/data/by_language/java.md"><img src="https://img.shields.io/badge/Java-1-007396"></a>
      <a href="/data/summary.md#languages">
        <img src="https://img.shields.io/badge/🌐%20All%20Languages-purple" alt="All Languages">
      </a>
    </p>
  </div>
  <div>
    <h3>💵 By Currency</h3>
    <p>
      <a href="/data/by_currency/erg.md"><img src="https://img.shields.io/badge/ERG-Ergo-orange" alt="ERG"></a>
      <a href="/data/by_currency/sigusd.md"><img src="https://img.shields.io/badge/SigUSD-Stablecoin-blue" alt="SigUSD"></a>
      <a href="/data/summary.md#currencies"><img src="https://img.shields.io/badge/🌐%20All%20Currencies-purple" alt="All Currencies"></a>
    </p>
  </div>
  <div>
    <h3>🏢 By Organization</h3>
    <p>
      <a href="/data/summary.md#projects">
        <img src="https://img.shields.io/badge/🌐%20All%20Organizations-purple" alt="All Organizations">
      </a>
    </p>
  </div>
 <!-- <h2>👨‍💻 For Developers</h2>
  <p>
    <a href="/data/all.md?filter=beginner"><img src="https://img.shields.io/badge/🔰%20Beginner%20Friendly-8-28A745" alt="Beginner Friendly"></a>
    <a href="/docs/ongoing-programs.md"><img src="https://img.shields.io/badge/📋%20Ongoing%20Programs-FF5722" alt="Ongoing Programs"></a>
  </p>-->
  <h2>⚙️ Automation & Maintenance</h2>
  <p><em>This repository is updated daily at Midnight UTC via GitHub Actions</em></p>
  <p>
    <a href="/data/currency_prices.md"><img src="https://img.shields.io/badge/💹%20Current%20Rates-00BCD4" alt="Currency Rates"></a>
    <a href="/docs/how-it-works.md"><img src="https://img.shields.io/badge/🔧%20How%20It%20Works-795548" alt="How It Works"></a>
    <a href="/docs/donate.md"><img src="https://img.shields.io/badge/❤️%20Donate-F44336" alt="Donate"></a>
   <!--  <a href="https://github.com/ergoplatform/Ergo-Bounties"><img src="https://img.shields.io/badge/⭐%20Star%20on%20GitHub-333333" alt="Star on GitHub"></a>-->
  </p>
</div>

## Quick Links

- Browse: [all bounties](/data/all.md), [new](/data/new-bounties.md), [recently active](/data/recently-active.md), [stale](/data/stale-bounties.md), [starter-sized](/data/starter-bounties.md), [high value](/data/high-value-bounties.md)
- Claim or reserve: open a PR adding one `submissions/*.json` file with `status: in-progress`
- Request payment: update that submission PR to `status: awaiting-review` once the upstream work PR is merged
- Maintainers: use [maintainer runbook](/docs/maintainer-runbook.md), [reviewer guide](/docs/reviewer-guide.md), [payment status](/submissions/payment_status.md), [payment queue](/submissions/payment_queue.md), and [triage dashboard](/submissions/triage.md)
- Automation details: [how it works](/docs/how-it-works.md)

## Source Files vs Generated Files

Edit source inputs, not generated bounty pages.

- Edit tracked sources: `src/config/tracked_repos.json`, `src/config/tracked_orgs.json`, `src/config/extra_bounties.json`, `submissions/*.json`, `src/**`, and `docs/**`.
- Do not manually edit generated outputs: `data/*.md`, `data/by_language/*.md`, `data/by_currency/*.md`, `data/by_org/*.md`, `submissions/payment_status.md`, `submissions/payment_queue.md`, `submissions/paid.md`, or generated README badges.
- Regenerate and validate locally with `./scripts/run_live_update.sh` or `./test.sh` after source changes.

<!-- Latest Update: 2026-06-18 -->
