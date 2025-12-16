<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Generated on: 2025-12-16 02:00:26 -->

# Currency Prices

*Report generated: 2025-12-16 02:00:26 UTC*

## Navigation

[![All Bounties](https://img.shields.io/badge/All%20Bounties-116-blue)](all.md) [![By Language](https://img.shields.io/badge/By%20Language-7-green)](summary.md#languages) [![By Currency](https://img.shields.io/badge/By%20Currency-7-yellow)](summary.md#currencies) [![By Organization](https://img.shields.io/badge/By%20Organization-9-orange)](summary.md#projects)

## Current Prices

| Currency | ERG Equivalent | Notes |
|----------|----------------|-------|
| [BENE ($1)](by_currency/bene.md) | 2.209598 | Each BENE is worth $1 in ERG |
| [GORT (Governance Token)](by_currency/gort.md) | 0.040638 | Governance token for ErgoDEX |
| [RSN (Governance Token)](by_currency/rsn.md) | 0.037809 | Governance token for Rosen Bridge |
| [SigUSD ($1)](by_currency/sigusd.md) | 2.209598 | Stablecoin pegged to USD |
| [Gold (per gram)](by_currency/gold.md) | 32.585462 | Price per gram of gold in ERG |

*Note: These prices are used to calculate ERG equivalents for bounties paid in different currencies.*

## How Prices are Retrieved

The currency prices are retrieved using different APIs:

### Spectrum API

SigUSD, GORT, and RSN prices are retrieved from the [Spectrum.fi](https://spectrum.fi/) API:

```
GET https://api.spectrum.fi/v1/price-tracking/markets
```

The API returns market data for various trading pairs. We filter this data to find specific currency pairs:

- For SigUSD: We look for markets where `quoteSymbol=SigUSD` and `baseSymbol=ERG`
- For GORT: We look for markets where `quoteSymbol=GORT` and `baseSymbol=ERG`
- For RSN: We look for markets where `quoteSymbol=RSN` and `baseSymbol=ERG`

### BENE

BENE price is set to be equivalent to SigUSD (which is pegged to USD), making 1 BENE equal to $1 worth of ERG.

### Gold Price from Oracle Pool

The price of gold (g GOLD) is retrieved from the XAU/ERG oracle pool using the Ergo Explorer API:

```
GET https://api.ergoplatform.com/api/v1/boxes/unspent/byTokenId/3c45f29a5165b030fdb5eaf5d81f8108f9d8f507b31487dd51f4ae08fe07cf4a
```

This queries for unspent boxes containing the oracle pool NFT. The price is extracted from the R4 register of the latest box.



---

<div align="center">
  <p>
    <a href="../docs/donate.md"><img src="https://img.shields.io/badge/❤️%20Donate-F44336" alt="Donate"></a>
    <a href="../docs/bounty-submission-guide.md#reserving-a-bounty"><img src="https://img.shields.io/badge/🔒%20How%20To%20Claim-4CAF50" alt="Claim a Bounty"></a>
  </p>
</div>


<!-- END OF GENERATED CONTENT -->
