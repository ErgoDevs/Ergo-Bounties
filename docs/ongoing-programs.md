# 🔄 Ongoing Reward Programs

In addition to specific bounties, the Ergo ecosystem offers ongoing reward programs to encourage continuous contributions in key areas. These programs provide opportunities for contributors to receive rewards for their work even if there isn't a specific bounty listed.

## Current Ongoing Programs

|Organisation|Repository|Title & Link|Primary Language|Value|ERG Value|Paid In|Reserve|
|---|---|---|---|---|---|---|---|
| [EF_DAO_LLC](../bounties/by_org/ef_dao_llc.md) | [educational-rewards](https://github.com/EF_DAO_LLC/educational-rewards) | [Educational Reward Program](https://docs.ergoplatform.com/contribute/) | Various | Varies | Based on contribution | ERG | [<kbd>Details</kbd>](#educational-reward-program) |
| [EF_DAO_LLC](../bounties/by_org/ef_dao_llc.md) | [development-rewards](https://github.com/EF_DAO_LLC/development-rewards) | [Development Reward Program](https://docs.ergoplatform.com/contribute/) | Various | Varies | Based on contribution | ERG | [<kbd>Details</kbd>](#development-reward-program) |



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
