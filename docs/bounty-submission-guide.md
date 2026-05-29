# Bounty Submission Guide

## Prerequisites

Before submitting a claim, ensure you have:

1. Completed work for a bounty or made a contribution to the Ergo ecosystem
2. Submitted and had your PR merged in the relevant repository
3. A wallet address where you can receive payment

## Reserving a Bounty

### Why Reserve Bounties?

Reserving a bounty helps:
- Prevent duplicate effort from multiple contributors
- Signal to maintainers that progress is being made
- Give you a reasonable timeframe to complete the work
- Establish a first-come, first-served system for popular bounties

### Quick Method (Using the UI)

1. Navigate to the bounty you want to work on in the [bounties list](/data/all.md)
2. Click the "Claim" button next to the bounty
3. This opens a pre-filled submission file/PR flow where available
4. Set `status` to `in-progress`, add `expected_completion`, and leave `work_link` empty until work is complete
5. Open the PR. The triage bot will validate it and mark the bounty reserved while the PR stays open.

### Manual Method (Using JSON)

1. **First, check if the bounty is already reserved**:
   - Review [open pull requests](https://github.com/ErgoDevs/Ergo-Bounties/pulls) and [submission triage](/submissions/triage.md) to see if anyone is already working on your target bounty
   - Check the original bounty issue/repository as well, as not everyone may use this central repository
   - PRs with "[WIP]" in the title indicate in-progress work

2. **Create a submission file**:
   - Follow the same process as normal submissions, but mark it as in-progress
   - Use the same JSON template, with these differences:
     ```json
     {
       // ... other fields remain the same
       "work_link": "", // Leave empty until work is complete
       "status": "in-progress", // This indicates it's a reservation
       "submission_date": "", // Leave empty until work is complete
       "expected_completion": "YYYY-MM-DD", // Add your estimated completion date
       "description": "Brief description of your planned approach or progress updates"
     }
     ```

3. **Submit as a PR**:
   - Title format: `[WIP] Bounty owner/repo#issue - Brief description`
   - Example: `[WIP] Bounty ergoplatform/sigmastate-interpreter#1053 - FSM Test Implementation`

4. **Work on your implementation**:
   - The open PR serves as your reservation
   - You can update the PR description or JSON file with progress updates if you wish

## Step-by-Step Submission Process

### Quick Method (Using the UI)

Once you've completed the work for a bounty, follow these steps to submit your solution:

1. Ensure your work meets all the requirements specified in the bounty
2. Create a pull request (PR) to the repository with your solution
3. In your PR description, reference the original bounty issue number
4. If you previously reserved the bounty, also reference your reservation issue
5. Wait for the project maintainers to review your submission

### Manual Method (Using JSON)

#### 1. Fork & Clone the Repository

```bash
git clone https://github.com/ErgoDevs/Ergo-Bounties.git
cd Ergo-Bounties
```

#### 2. Create a JSON Submission File

Create a new JSON file in the `submissions/` directory with the naming convention:

```
{github_username}-{descriptive-name}.json
```

For example:
```
user123-ergoscript-fsmtest.json
```

#### 3. Fill Out the JSON File

Copy the template from `submissions/example-user-ergoscript-fsmtest.json` and fill in your details:

```json
{
  "contributor": "user123",
  "wallet_address": "9fABC123...",
  "contact_method": "Discord: user123#1234",
  "work_link": "https://github.com/ergoplatform/sigmastate-interpreter/pull/1100",
  "work_title": "ErgoScript FSM Test Implementation",
  "bounty_id": "sigmastate-interpreter#1053",
  "original_issue_link": "https://github.com/ergoplatform/sigmastate-interpreter/issues/1053",
  "payment_currency": "ERG",
  "bounty_value": 200.00,
  "status": "awaiting-review",
  "submission_date": "2025-03-13",
  "description": "Implemented ErgoScript version of the finite state machine test.",
  
  "review_notes": "",
  "payment_tx_id": "",
  "payment_date": ""
}
```

##### Required Fields

- **contributor**: Your GitHub username
- **wallet_address**: The address where payment should be sent
- **work_link**: Link to the PR where the work was completed
- **work_title**: A short title describing the work
- **payment_currency**: Currency for payment (e.g., ERG, SigUSD, RSN)
- **bounty_value**: The payment amount (numeric value, based on currency)
- **status**: Set this to `awaiting-review`. Allowed statuses are `in-progress`, `awaiting-review`, `reviewed`, `paid`. A GitHub Action will validate this.
- **submission_date**: Date of submission (YYYY-MM-DD)

##### Recommended Fields

- **bounty_id**: The GitHub issue number in `owner/repo#issue_number` format. Legacy `repo#issue_number` values may appear in older files, but new submissions should use the full form.
- **contact_method**: A way for reviewers to reach out if they have questions
- **original_issue_link**: The full URL to the original issue or bounty
- **description**: A brief summary of the work completed

##### Fields for Reviewers / Automation (Leave Empty)

- **reviewer**: GitHub username of the original issue author. This field is automatically added by a bot when you open your Pull Request.
- **review_notes**: Will be filled by reviewers during the review process.
- **payment_tx_id**: Will be filled after payment is processed.
- **payment_date**: Will be filled after payment is processed.

#### 4. Commit & Push Changes

```bash
git add submissions/user123-ergoscript-fsmtest.json
git commit -m "Submission for ErgoScript FSM Test Implementation"
git push origin main
```

#### 5. Open a Pull Request

1. Go to GitHub and open a pull request with a descriptive title
2. Provide a brief summary in the PR description
3. Ensure all details in your JSON file are correct

## Review Process

1. Submit your PR with status `awaiting-review`.
2. A GitHub Action (`triage-submission-prs.yml`) validates the submission, labels the PR, comments with required fixes, checks the linked upstream PR merge state, and requests/tags a reviewer where possible.
3. Maintainers review your submission.
4. They will verify:
   - The work has been completed as per requirements.
   - The PR has been merged in the target repository (if applicable).
   - The bounty value matches what was advertised.
5. If changes are needed, maintainers may update the status to `in-progress` or request changes.
6. Once approved, maintainers will update the status to `reviewed`.
7. The PR containing the submission JSON is merged.
8. Reviewed submissions appear in [payment queue](/submissions/payment_queue.md).
9. Payment will be processed based on the JSON details.
10. The status is updated to `paid` with `payment_tx_id` and `payment_date`.

## Payment Process

1. After the submission PR (with status `reviewed`) is merged, it appears in `submissions/payment_queue.md`.
2. An authorized person processes the payment.
3. They update your submission file (usually via a direct commit or separate PR) with:
   - `status`: Changed to `paid`
   - `payment_tx_id`: The transaction ID
   - `payment_date`: The date of payment
4. The `update-payment-status` workflow updates `payment_status.md`, `payment_queue.md`, and `paid.md`.

## Tips for Successful Submissions

- Read the bounty description carefully to understand all requirements
- Ask questions in the bounty issue if anything is unclear
- Provide thorough documentation with your submission
- Include tests where appropriate
- Be responsive to feedback and requests for changes

## Troubleshooting

If you encounter issues with your submission:

1. Check the PR comments for feedback from reviewers
2. Check labels such as `missing-wallet`, `upstream-unmerged`, `stale-reservation`, `duplicate-bounty`, or `invalid-submission`
3. Make any requested changes to your submission
4. If your PR is closed without merging, create a new PR with corrections

## Resources for Help

- Ask in the original bounty issue
- Open an issue in the Ergo-Bounties repository
- Join the [Ergo Discord](https://discord.gg/f6DNycM9sS) and ask in the appropriate channel
- Contact the bounty creator directly through GitHub
