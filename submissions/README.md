<div align="center">
  <h1>📝 Bounty Submissions</h1>
  <p><strong>Repository of all bounty claims and reservations for the Ergo ecosystem</strong></p>
  <p>
    <a href="../docs/bounty-submission-guide.md"><img src="https://img.shields.io/badge/Documentation-Submission%20Guide-blue" alt="Documentation"></a>
    <a href="../CONTRIBUTING.md"><img src="https://img.shields.io/badge/Contributions-Welcome-orange" alt="Contributions Welcome"></a>
  </p>
</div>

## 🌟 Overview

This directory contains all bounty submissions for the Ergo ecosystem. Each submission is a JSON file that follows a specific format and naming convention.

## 🚀 Bounty Process

- **Reserving a Bounty**: Submit a PR with a JSON file marked as `in-progress` to claim a bounty before starting work
- **Submitting Work**: Create or update a PR with your completed work details and set status to `awaiting-review`

Both processes use the same JSON template and PR workflow. Reservations are first-come, first-served.

**[📝 View the Detailed Submission Guide →](../docs/bounty-submission-guide.md)**

## JSON File Format

Each submission must include the following required fields:

- `contributor`: Your GitHub username
- `wallet_address`: The address where payment should be sent
- `work_link`: Link to the PR where the work was completed
- `work_title`: A short title describing the work
- `payment_currency`: Currency for payment (e.g., ERG, SigUSD, RSN)
- `bounty_value`: The payment amount (numeric value)
- `status`: Current submission status (`in-progress`, `awaiting-review`, `reviewed`, `paid`). A GitHub Action will validate this on PRs.
- `submission_date`: Date of submission (leave empty for reservations)
- `expected_completion`: Estimated completion date (for reservations)

Additional recommended fields:

- `bounty_id`: The GitHub issue number in `{repo}#{issue_number}` format (if applicable)
- `contact_method`: A way for reviewers to reach out if they have questions
- `original_issue_link`: The full URL to the original issue or bounty
- `description`: A brief summary of the work completed

The following fields will be filled out by reviewers or automation:

- `reviewer`: GitHub username of the original issue author (automatically added by bot when PR is opened)
- `review_notes`: Notes from the reviewer
- `payment_tx_id`: Transaction ID of the payment
- `payment_date`: Date when payment was processed

## Example

See the [submission template](example-user-ergoscript-fsmtest.json) for a complete example.

## Review Process

1. Submit your PR with status `awaiting-review`.
2. A GitHub Action (`validate-submission-status.yml`) checks if the status is valid.
3. Maintainers review your submission.
4. If changes are needed, maintainers may update the status to `in-progress` or request changes.
5. Once approved, maintainers will update the status to `reviewed`.
6. The PR is merged.
7. Payment is processed based on the JSON details.
8. The status is updated to `paid` (usually via separate process or manually).

For more detailed instructions, see the [submission guide](../docs/bounty-submission-guide.md).
