<div align="center">
  <h1>🏆 Ergo Ecosystem Bounties</h1>
  <p><strong>The central hub for tracking, claiming, and managing bounties across the Ergo blockchain ecosystem</strong></p>
  <p>
    <a href="/bounties/all.md"><img src="https://img.shields.io/badge/Open%20Bounties-100+-brightgreen" alt="Open Bounties"></a>
    <a href="/docs/submission-guide.md"><img src="https://img.shields.io/badge/Documentation-Submission%20Guide-blue" alt="Documentation"></a>
    <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/Contributions-Welcome-orange" alt="Contributions Welcome"></a>
  </p>
</div>

## 🌟 Overview

Ergo Ecosystem Bounties offers financial incentives to developers who contribute to the Ergo blockchain ecosystem by implementing features, fixing bugs, or improving documentation. This repository serves as the central coordination point for all bounty-related activities.

- **Browse open bounties** to find work that matches your skills
- **Reserve bounties** to prevent duplicate work
- **Submit completed work** to claim rewards
- **Add missing bounties** to help grow the ecosystem

## 📋 Open Bounties

<div align="center">
  <h2>
    <a href="/bounties/all.md">
      <img src="https://img.shields.io/badge/View%20All%20Current%20Bounties-→-success?style=for-the-badge" alt="View All Current Bounties">
    </a>
  </h2>
</div>

### Explore Bounties

<div align="center">
  <p>
    <a href="/bounties/all.md#summary"><img src="https://img.shields.io/badge/View%20Bounty%20Distribution%20by%20Project-→-orange?style=for-the-badge" alt="View Bounty Distribution by Project"></a>
  </p>
  
  <p>
    <a href="/bounties/all.md#detailed-bounties"><img src="https://img.shields.io/badge/Browse%20Featured%20Opportunities-→-yellow?style=for-the-badge" alt="Browse Featured Opportunities"></a>
  </p>
</div>

### Browse by Programming Language

<div align="center">
  <p>Find tasks that match your skills and expertise:</p>
  
  <div style="margin: 20px 0;">
    <a href="/bounties/by_language/scala.md"><img src="https://img.shields.io/badge/Scala-42%20Bounties-DC322F" alt="Scala Bounties"></a>
    <a href="/bounties/by_language/rust.md"><img src="https://img.shields.io/badge/Rust-28%20Bounties-B7410E" alt="Rust Bounties"></a>
    <a href="/bounties/by_language/javascript.md"><img src="https://img.shields.io/badge/JavaScript-15%20Bounties-F7DF1E" alt="JavaScript Bounties"></a>
    <a href="/bounties/by_language/typescript.md"><img src="https://img.shields.io/badge/TypeScript-8%20Bounties-3178C6" alt="TypeScript Bounties"></a>
    <a href="/bounties/by_language/python.md"><img src="https://img.shields.io/badge/Python-5%20Bounties-3776AB" alt="Python Bounties"></a>
    <a href="/bounties/by_language/java.md"><img src="https://img.shields.io/badge/Java-2%20Bounties-007396" alt="Java Bounties"></a>
  </div>
  
  <p>
    <a href="/bounties/by_language/"><img src="https://img.shields.io/badge/View%20All%20Languages-→-purple?style=for-the-badge" alt="View All Languages"></a>
  </p>
</div>

<div align="center">
  <p>
    <a href="/bounties/all.md"><img src="https://img.shields.io/badge/High%20Value-10+%20Bounties%20Over%201000%20ERG-gold" alt="High Value Bounties"></a>
    <a href="/bounties/all.md"><img src="https://img.shields.io/badge/Beginner%20Friendly-15+%20Bounties-success" alt="Beginner Friendly"></a>
    <a href="/bounties/all.md"><img src="https://img.shields.io/badge/Updated%20Daily-Automated-informational" alt="Updated Daily"></a>
  </p>
</div>

<div class="note" style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0; border-radius: 4px;">
  <strong>Note:</strong> Bounties are updated daily via GitHub Actions. Values shown in ERG equivalent. Some bounties may be paid in other tokens as noted in the detailed listings.
</div>

## 🚀 Bounty Process

This repository uses a PR-based system for both reserving and submitting bounties:

<table>
  <tr>
    <td width="50%"><strong>Reserving a Bounty</strong></td>
    <td>Submit a PR with a JSON file marked as <code>in-progress</code> to claim a bounty before starting work</td>
  </tr>
  <tr>
    <td><strong>Submitting Work</strong></td>
    <td>Create or update a PR with your completed work details and set status to <code>awaiting-review</code></td>
  </tr>
</table>

Both processes use the same JSON template and PR workflow. Reservations are first-come, first-served.

<div align="center">
  <p>
    <a href="/docs/submission-guide.md"><img src="https://img.shields.io/badge/📝%20View%20Detailed%20Submission%20Guide-→-blue?style=for-the-badge" alt="View Detailed Submission Guide"></a>
  </p>
</div>

## 🔍 Adding a Missing Bounty

Know of a bounty that's not listed? You can help add it to our tracking system by submitting a PR to add the repository to `tracked_repos.json`. Our automated system will then include its bounties in the next update.

<div align="center">
  <p>
    <a href="/docs/submission-guide.md"><img src="https://img.shields.io/badge/📝%20Guide%20for%20Adding%20Bounties-→-blue?style=for-the-badge" alt="Guide for Adding Bounties"></a>
  </p>
</div>

## 🤖 Automated Bounty Tracking System

<div align="center">
  <p>
    <a href="/docs/how-it-works.md"><img src="https://img.shields.io/badge/GitHub%20Actions-Powered-2088FF" alt="GitHub Actions"></a>
    <a href="/docs/how-it-works.md"><img src="https://img.shields.io/badge/Daily%20Updates-Midnight%20UTC-blueviolet" alt="Daily Updates"></a>
    <a href="/tracked_repos.json"><img src="https://img.shields.io/badge/Tracked%20Repos-25+-yellow" alt="Tracked Repos"></a>
  </p>
</div>

This repository uses GitHub Actions to automatically track and update bounties across the Ergo ecosystem. The system:

- Scans repositories for issues with bounty tags
- Extracts bounty amounts and details
- Generates updated reports daily
- Categorizes bounties by language and project

<div align="center">
  <p>
    <a href="/docs/how-it-works.md"><img src="https://img.shields.io/badge/🔧%20Learn%20How%20It%20Works-→-blue?style=for-the-badge" alt="Learn How It Works"></a>
  </p>
</div>


## 💰 Donations

<div class="donation-box" style="background-color: #f8f9fa; border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px;">
  <p>The Ergo ecosystem bounty program is supported by donations. Your contributions help:</p>
  
  <ul>
    <li>Fund Ergo core development</li>
    <li>Improve ecosystem tooling</li>
    <li>Promote Ergo technology among developers</li>
    <li>Increase bounty rewards</li>
  </ul>

  <div align="center" style="margin-top: 15px;">
    <table>
      <tr>
        <td align="center"><strong>Multi-sig Wallet</strong></td>
        <td align="center"><strong>Paideia Wallet</strong></td>
      </tr>
      <tr>
        <td align="center">
          <a href="https://ergexplorer.com/addresses#2BggBDgr9nBXyMpT5NbZf1QRN2pfHmzJxWwcfGEsgqzs94TEJv5GmtKTjmew74DjoTjTULa2A4RjJW6qGvniFm29KZKZ4attHxSZxuq1hQnXbURvoYm7jkHHzrd4ZF9u29cgHZczv2LWNiHoU6seFkC73JvGkT1khxkzRatPwDZ6aP87VPV6F4b1XmsitCB2DoKCYEtgtP1yCXmDhfSgdzDatn4SjSfZkxysggBH3TzJqTzZkqn8pp1DeAdiPJ1JZr8KeUGpnjkpjddoc">
            <img src="https://img.shields.io/badge/Donate-Multi--sig%20Wallet-ff69b4?style=for-the-badge" alt="Multi-sig Wallet">
          </a>
        </td>
        <td align="center">
          <a href="https://ergexplorer.com/addresses#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">
            <img src="https://img.shields.io/badge/Donate-Paideia%20Wallet-ff69b4?style=for-the-badge" alt="Paideia Wallet">
          </a>
        </td>
      </tr>
    </table>
  </div>
</div>
