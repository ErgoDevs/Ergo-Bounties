# 🔄 Ongoing Reward Programs

In addition to specific bounties, the Ergo ecosystem offers ongoing reward programs to encourage continuous contributions in key areas. These programs provide opportunities for contributors to receive rewards for their work even if there isn't a specific bounty listed.

## Current Ongoing Programs

<!-- BEGIN_ONGOING_PROGRAMS_TABLE -->
| Organization | Program | Details | Primary Language |
|-------------|---------|---------|------------------|
| [EF_DAO_LLC](by_org/ef_dao_llc.md) | [Educational Reward Program](#-educational-reward-program) | [Details](#-educational-reward-program) | [Various](by_language/various.md) |
| [EF_DAO_LLC](by_org/ef_dao_llc.md) | [Development Reward Program](#-development-reward-program) | [Details](#-development-reward-program) | [Various](by_language/various.md) |

<!-- END_ONGOING_PROGRAMS_TABLE -->

## Grants and Additional Bounties

<!-- BEGIN_ACTIVE_BOUNTIES_TABLE -->
These grants and additional bounties are pulled from src/config/extra_bounties.json:

|Organisation|Repository|Title & Link|Bounty Amount|Paid in|Primary Language|Reserve|
|---|---|---|---|---|---|---|
| [DevDAO](by_org/devdao.md) | [github.com/Alesfatalis/keystone-sdk-rust/tree/feat/ergo_support](https://github.com/Alesfatalis/keystone-sdk-rust/tree/feat/ergo_support) | [Keystone Wallet Integration](https://discord.com/channels/668903786361651200/669989266478202917/1344310506277830697) | 3000  | [ERG](by_currency/erg.md) | [Rust](by_language/rust.md) | <kbd>In Progress</kbd> |
| [fleet-sdk](by_org/fleet-sdk.md) | [docs](https://github.com/fleet-sdk/docs) | [[Educational] Fleet-Tutorial + Bounties](https://github.com/fleet-sdk/docs/issues/8) | 775 (967.97 ERG) | [SigUSD](by_currency/sigusd.md) | [Various](by_language/various.md) | [<kbd>Reserve</kbd>](https://github.com/ErgoDevs/Ergo-Bounties/new/main?filename=submissions/fleet-sdk-docs-8.json&value=%7B%0A%20%20%22contributor%22%3A%20%22YOUR_GITHUB_USERNAME%22%2C%0A%20%20%22wallet_address%22%3A%20%22YOUR_WALLET_ADDRESS%22%2C%0A%20%20%22contact_method%22%3A%20%22YOUR_CONTACT_INFO%22%2C%0A%20%20%22work_link%22%3A%20%22%22%2C%0A%20%20%22work_title%22%3A%20%22%5BEducational%5D%20Fleet-Tutorial%20%2B%20Bounties%22%2C%0A%20%20%22bounty_id%22%3A%20%22fleet-sdk/docs%238%22%2C%0A%20%20%22original_issue_link%22%3A%20%22https%3A//github.com/fleet-sdk/docs/issues/8%22%2C%0A%20%20%22payment_currency%22%3A%20%22SigUSD%22%2C%0A%20%20%22bounty_value%22%3A%20775.0%2C%0A%20%20%22status%22%3A%20%22in-progress%22%2C%0A%20%20%22submission_date%22%3A%20%22%22%2C%0A%20%20%22expected_completion%22%3A%20%22YYYY-MM-DD%22%2C%0A%20%20%22description%22%3A%20%22I%20am%20working%20on%20this%20bounty%22%2C%0A%20%20%22review_notes%22%3A%20%22%22%2C%0A%20%20%22payment_tx_id%22%3A%20%22%22%2C%0A%20%20%22payment_date%22%3A%20%22%22%0A%7D&message=Claim%20Bounty%20fleet-sdk/docs%238&description=I%20want%20to%20claim%20this%20bounty%20posted%20by%20fleet-sdk.%0A%0ABounty:%20%5BEducational%5D%20Fleet-Tutorial%20%2B%20Bounties) |

<!-- END_ACTIVE_BOUNTIES_TABLE -->


## 📚 Educational Reward Program

The Educational Reward Program is designed to stimulate the creation of educational content that benefits the Ergo community. We believe in the power of knowledge-sharing and empowerment as key drivers of growth.

### Program Details

- **Focus Area**: Developer Tutorials and Guides
- **Eligibility**: Contributors of all skill levels
- **Reward**: Varies based on contribution quality and impact
- **Currency**: ERG

### How to Participate

If you have educational content, even if it's not explicitly mentioned here, it could still be eligible for a reward. We invite you to contribute any educational materials that can enrich learning experiences.

To claim a reward for your educational contribution:

1. **Complete your educational content**:
   - Create tutorials, guides, explainers, or other educational materials
   - Publish your content (on your blog, GitHub, YouTube, etc.)
   - Ensure it provides value to the Ergo community

2. **Submit a claim through this repository**:
   - Fork this repository
   - Create a new JSON file in the `submissions/` directory with the naming convention:
     ```
     {github_username}-educational-{descriptive-name}.json
     ```
   - Fill out the JSON file using the template below:
     ```json
     {
       "contributor": "your-github-username",
       "wallet_address": "your-ergo-wallet-address",
       "contact_method": "Discord: username#1234",
       "work_link": "https://link-to-your-educational-content",
       "work_title": "Title of Your Educational Content",
       "bounty_id": "program-edu",
       "original_issue_link": "https://github.com/ErgoDevs/Ergo-Bounties/blob/main/docs/ongoing-programs.md",
       "payment_currency": "ERG",
       "bounty_value": 0,
       "status": "awaiting-review",
       "submission_date": "YYYY-MM-DD",
       "description": "Detailed description of your educational content and its value to the Ergo community."
     }
     ```
   - Note: Leave the `bounty_value` as 0 - the reviewers will determine the appropriate reward based on the quality and impact of your contribution.
   - Submit a PR with the title: `[EDUCATIONAL] Title of Your Educational Content`

3. **Review Process**:
   - Maintainers will review your submission
   - They will evaluate the quality, depth, and impact of your educational content
   - If approved, they will assign a reward value and merge your PR
   - Payment will be processed based on the details in your JSON file

## 💻 Development Reward Program

The Development Reward Program acknowledges and appreciates significant contributions to the Ergo repositories. This program rewards developers who help improve and enhance the Ergo ecosystem through code contributions.

### Program Details

- **Focus Area**: Ergo repositories and ecosystem projects
- **Eligibility**: Contributors who make significant improvements
- **Reward**: Varies based on contribution impact
- **Currency**: ERG

### How to Participate

If your contributions have significantly enhanced the development and improvement of the Ergo ecosystem, you could be eligible for a reward.

To claim a reward for your development contribution:

1. **Complete your development work**:
   - Make significant contributions to Ergo repositories
   - Ensure your PR is merged in the target repository
   - Verify your work has a meaningful impact on the ecosystem

2. **Submit a claim through this repository**:
   - Fork this repository
   - Create a new JSON file in the `submissions/` directory with the naming convention:
     ```
     {github_username}-development-{descriptive-name}.json
     ```
   - Fill out the JSON file using the template below:
     ```json
     {
       "contributor": "your-github-username",
       "wallet_address": "your-ergo-wallet-address",
       "contact_method": "Discord: username#1234",
       "work_link": "https://github.com/ergoplatform/repo/pull/999",
       "work_title": "Title of Your Development Contribution",
       "bounty_id": "program-dev",
       "original_issue_link": "https://github.com/ErgoDevs/Ergo-Bounties/blob/main/docs/ongoing-programs.md",
       "payment_currency": "ERG",
       "bounty_value": 0,
       "status": "awaiting-review",
       "submission_date": "YYYY-MM-DD",
       "description": "Detailed description of your development contribution, its impact, and why it deserves a reward."
     }
     ```
   - Note: Leave the `bounty_value` as 0 - the reviewers will determine the appropriate reward based on the significance and impact of your contribution.
   - Submit a PR with the title: `[DEVELOPMENT] Title of Your Development Contribution`

3. **Review Process**:
   - Maintainers will review your submission
   - They will evaluate the significance and impact of your development contribution
   - If approved, they will assign a reward value and merge your PR
   - Payment will be processed based on the details in your JSON file

## Why Participate?

We deeply appreciate the time, dedication, and expertise you invest in enhancing our ecosystem. By participating in our mission to improve educational materials and drive development within the Ergo community, you are playing a crucial role in the collective growth and success of the platform.

These ongoing programs complement our specific bounties and provide additional avenues for contributors to be rewarded for their valuable work.

## About This Page

This page is organized into several sections:

1. **Current Ongoing Programs** - These are continuous reward programs without a fixed bounty amount, where rewards are determined based on the quality and impact of contributions.

2. **Grants and Additional Bounties** - These are specific bounties or grants that have been manually added to `src/config/extra_bounties.json`. They include:
   - Special grants that aren't associated with GitHub issues
   - Bounties from platforms outside GitHub (e.g., Discord announcements)
   - Bounties that need manual tracking for status updates

   Each entry includes its current status:
   - **Open** - Available for claiming (shows a "Reserve" button)
   - **In Progress** - Already being worked on (shows "In Progress" text)

If you'd like to add a new grant or bounty to this page:

1. Fork this repository
2. Edit the `src/config/extra_bounties.json` file with the new entry
3. Include a `"status": "Open"` field (or "In Progress" if already claimed)
4. Submit a PR with the title: `[ADD MANUAL BOUNTY] Bounty Title`

For more details on the technical implementation, see the [How It Works](/docs/how-it-works.md#adding-manual-bounties-and-grants) guide.
