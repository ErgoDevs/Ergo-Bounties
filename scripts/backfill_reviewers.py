import os
import json
import time
import requests
import re
from pathlib import Path

SUBMISSIONS_DIR = Path("submissions")
IGNORE_FILES = {"example-user-ergoscript-fsmtest.json"}
GITHUB_TOKEN = "os.environ.get("GITHUB_TOKEN") # Or use PAT_TOKEN if needed"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
API_DELAY_SECONDS = 1 # Add delay to avoid hitting rate limits

def parse_github_url(url):
    """Parses a GitHub issue/PR URL to extract owner, repo, and number."""
    if not url:
        return None, None, None
    # Regex to handle both issues and pull requests
    match = re.match(r"https?://github\.com/([\w.-]+)/([\w.-]+)/(?:issues|pull)/(\d+)", url)
    if match:
        owner, repo, number = match.groups()
        return owner, repo, int(number)
    print(f"Warning: Could not parse GitHub URL: {url}")
    return None, None, None

def get_issue_author(owner, repo, issue_number):
    """Fetches the author of a GitHub issue using the API."""
    if not all([owner, repo, issue_number, GITHUB_TOKEN]):
        print("Warning: Missing owner, repo, issue_number, or GITHUB_TOKEN. Cannot fetch author.")
        return None

    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    try:
        print(f"Fetching issue: {api_url}")
        response = requests.get(api_url, headers=HEADERS)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        issue_data = response.json()
        author = issue_data.get("user", {}).get("login")
        if author:
            print(f"Found author: {author}")
            return author
        else:
            print(f"Warning: Could not find author in issue data for {owner}/{repo}#{issue_number}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching issue {owner}/{repo}#{issue_number}: {e}")
        if response.status_code == 404:
             print("Issue not found.")
        elif response.status_code == 403:
             print("Forbidden - Check GITHUB_TOKEN permissions or rate limits.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching issue {owner}/{repo}#{issue_number}: {e}")
        return None

def backfill_reviewer(filepath):
    """Reads a submission JSON, fetches the reviewer if missing, and updates the file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if reviewer already exists or if link is missing
        if data.get("reviewer"):
            print(f"Skipping {filepath.name}: Reviewer already exists ('{data['reviewer']}').")
            return False
        if not data.get("original_issue_link"):
            print(f"Skipping {filepath.name}: No original_issue_link found.")
            return False

        owner, repo, issue_number = parse_github_url(data["original_issue_link"])
        if not owner:
            print(f"Skipping {filepath.name}: Could not parse issue URL.")
            return False

        # Add delay before API call
        time.sleep(API_DELAY_SECONDS)

        author = get_issue_author(owner, repo, issue_number)
        if not author:
            print(f"Skipping {filepath.name}: Could not fetch issue author.")
            return False

        # Update data and write back
        data["reviewer"] = author
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n') # Add trailing newline
        print(f"Successfully updated {filepath.name} with reviewer: {author}")
        return True

    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath.name}")
        return False
    except Exception as e:
        print(f"Error processing {filepath.name}: {e}")
        return False

def main():
    """Main function to iterate through submissions and backfill reviewers."""
    print("Starting reviewer backfill process...")
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set. Cannot query GitHub API.")
        return

    updated_count = 0
    skipped_count = 0
    error_count = 0

    if not SUBMISSIONS_DIR.is_dir():
        print(f"Error: Submissions directory not found at {SUBMISSIONS_DIR}")
        return

    for filepath in SUBMISSIONS_DIR.glob("*.json"):
        if filepath.name in IGNORE_FILES:
            print(f"Ignoring file: {filepath.name}")
            continue

        print(f"\nProcessing file: {filepath.name}")
        try:
            updated = backfill_reviewer(filepath)
            if updated:
                updated_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"Critical error processing {filepath.name}: {e}")
            error_count += 1


    print("\n--- Backfill Summary ---")
    print(f"Files updated: {updated_count}")
    print(f"Files skipped (already had reviewer, no link, parse error, or fetch error): {skipped_count}")
    print(f"Files with critical processing errors: {error_count}")
    print("------------------------")

if __name__ == "__main__":
    main()
