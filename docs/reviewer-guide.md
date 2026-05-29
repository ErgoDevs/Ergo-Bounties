# Bounty Reviewer Guide

This guide outlines the process for reviewers (typically the original author of the bounty issue) after being tagged in a bounty submission pull request (PR) in the Ergo-Bounties repository.

## You've Been Tagged! What Now?

When a contributor submits a PR to claim a bounty for an issue you originally created, a GitHub Action (`triage-submission-prs.yml`) will automatically:

1. Validate the submission JSON.
2. Check that the linked work PR is merged when the claim is complete.
3. Add labels such as `ready-review`, `payment-ready`, `upstream-unmerged`, `missing-wallet`, or `stale-reservation`.
4. Add/update a triage comment on the PR.
5. Request you as reviewer or tag you when GitHub reviewer assignment is not possible.

This tag serves as a notification that a submission related to your bounty issue is ready for your input or review.

## Reviewer Responsibilities

As the original issue author and designated reviewer, your main responsibilities are:

1.  **Verify Completion:** Check the linked work in the submission (usually another PR in the relevant project repository) to ensure it adequately addresses the requirements of the original bounty issue.
2.  **Confirm Merge:** Ensure the contributor's work PR has been merged into the target repository for completed claims.
3.  **Approve the Submission:** If the work is satisfactory and merged, approve the submission PR in *this* (Ergo-Bounties) repository.
4.  **Update Status (Optional but Recommended):** While maintainers often handle final status updates, you can help by updating the `status` field in the submission JSON file within the PR branch to `reviewed` once you are satisfied. Commit this change to the PR branch.
    ```json
    {
      // ... other fields
      "status": "reviewed",
      // ... other fields
    }
    ```
5.  **Communicate:** Leave comments on the submission PR if changes are needed or if you have questions for the contributor.

## The Process Flow

1.  **Submission PR Opened:** Contributor opens PR with `status: awaiting-review`.
2.  **Automation Runs:**
    *   `triage-submission-prs.yml` validates fields, comments with findings, applies labels, checks duplicate/stale claims, and requests or tags reviewers.
    *   Scheduled triage writes `submissions/triage.md` for maintainers.
3.  **Your Review:** You review the linked work and the submission details.
4.  **Approval/Feedback:**
    *   **If Approved:** You approve the Ergo-Bounties PR. Optionally, update the status in the JSON to `reviewed`.
    *   **If Changes Needed:** Leave comments on the PR detailing the required changes. The contributor can then push updates.
5.  **Merge:** A repository maintainer merges the approved Ergo-Bounties PR (ideally with status `reviewed`).
6.  **Payment:** An authorized person processes the payment based on the merged JSON details.
7.  **Final Update:** The submission JSON is updated (usually via direct commit or another PR) with `status: paid`, `payment_tx_id`, and `payment_date`.
8.  **Report Update:** The `update-payment-status` workflow runs automatically, updating `submissions/payment_status.md`, `submissions/payment_queue.md`, and `submissions/paid.md`.

## Key Points

*   Your role is crucial in verifying that the bounty requirements were met.
*   Clear communication on the PR is important.
*   Updating the status to `reviewed` helps streamline the process for maintainers and payment processors.
*   Reviewed merged claims appear in `submissions/payment_queue.md`.

Thank you for contributing to the Ergo ecosystem by creating and reviewing bounties!
