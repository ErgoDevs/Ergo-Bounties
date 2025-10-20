# Bounty Reviewer Guide

This guide outlines the process for reviewers (typically the original author of the bounty issue) after being tagged in a bounty submission pull request (PR) in the Ergo-Bounties repository.

## You've Been Tagged! What Now?

When a contributor submits a PR to claim a bounty for an issue you originally created, a GitHub Action (`tag-author.yml`) will automatically:

1.  Add a comment to the PR tagging you (e.g., `FYI @your-username...`).
2.  Add your GitHub username to the `reviewer` field within the submission JSON file in the PR branch.

This tag serves as a notification that a submission related to your bounty issue is ready for your input or review.

## Reviewer Responsibilities

As the original issue author and designated reviewer, your main responsibilities are:

1.  **Verify Completion:** Check the linked work in the submission (usually another PR in the relevant project repository) to ensure it adequately addresses the requirements of the original bounty issue.
2.  **Confirm Merge (if applicable):** Ensure the contributor's work PR has been merged into the target repository.
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
    *   `tag-author.yml` tags you and adds your username to the `reviewer` field in the JSON.
    *   `validate-submission-status.yml` checks if the status is valid (it should be `awaiting-review` initially).
3.  **Your Review:** You review the linked work and the submission details.
4.  **Approval/Feedback:**
    *   **If Approved:** You approve the Ergo-Bounties PR. Optionally, update the status in the JSON to `reviewed`.
    *   **If Changes Needed:** Leave comments on the PR detailing the required changes. The contributor can then push updates.
5.  **Merge:** A repository maintainer merges the approved Ergo-Bounties PR (ideally with status `reviewed`).
6.  **Payment:** An authorized person processes the payment based on the merged JSON details.
7.  **Final Update:** The submission JSON is updated (usually via direct commit or another PR) with `status: paid`, `payment_tx_id`, and `payment_date`.
8.  **Report Update:** The `update-payment-status` workflow runs automatically, moving the entry from `submissions/payment_status.md` to `submissions/paid.md`.

## Key Points

*   Your role is crucial in verifying that the bounty requirements were met.
*   Clear communication on the PR is important.
*   Updating the status to `reviewed` helps streamline the process for maintainers and payment processors.

Thank you for contributing to the Ergo ecosystem by creating and reviewing bounties!
