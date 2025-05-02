import os
import sys # Import sys to modify path
import json
import time
import requests
import re
from pathlib import Path

# Add project root to sys.path to allow importing 'src'
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
from collections import defaultdict
from dotenv import load_dotenv
import datetime
# Import the label/text extractors AND the main bounty identification function
from src.core.extractors import extract_from_labels, extract_from_text, is_bounty_issue
from collections import Counter # Import Counter for statistics

# --- Configuration ---
load_dotenv()
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("PAT_TOKEN")
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
API_DELAY_SECONDS = 0.5 # Shorter delay, but be mindful of rate limits
ISSUES_PER_PAGE = 100 # Max allowed by GitHub API

CONFIG_DIR = Path("src/config")
TRACKED_ORGS_FILE = CONFIG_DIR / "tracked_orgs.json"
TRACKED_REPOS_FILE = CONFIG_DIR / "tracked_repos.json"
OUTPUT_FILE = Path("submissions/paid.md")
HISTORICAL_HEADER = "## Closed Bounties" # Simplified header variable name

# --- Helper Functions ---

def get_paginated_data(url):
    """Fetches all pages of data from a GitHub API endpoint."""
    results = []
    # Correctly append the first query parameter
    separator = '&' if '?' in url else '?'
    page_url = f"{url}{separator}per_page={ISSUES_PER_PAGE}"
    while page_url:
        try:
            print(f"Fetching: {page_url}") # Keep print for debugging this time
            response = requests.get(page_url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                results.extend(data)
            else: # Handle cases where a single object might be returned unexpectedly
                results.append(data)
                break # Stop pagination if it's not a list

            # Check for next page link
            page_url = response.links.get("next", {}).get("url")
            if page_url:
                time.sleep(API_DELAY_SECONDS) # Delay between pages
        except requests.exceptions.RequestException as e:
            print(f"Error fetching paginated data from {page_url}: {e}")
            if response is not None and response.status_code == 403:
                 print("Rate limit likely exceeded or token permissions issue.")
                 # Consider stopping or adding a longer delay here
            break # Stop pagination on error
        except Exception as e:
            print(f"Unexpected error during pagination for {page_url}: {e}")
            break
    return results

def get_org_repos(org_name):
    """Gets all repositories for a given organization."""
    print(f"Fetching repositories for organization: {org_name}")
    url = f"https://api.github.com/orgs/{org_name}/repos"
    repos = get_paginated_data(url)
    repo_names = [f"{org_name}/{repo['name']}" for repo in repos if repo.get('name')]
    print(f"Found {len(repo_names)} repositories for {org_name}.")
    return repo_names

def get_closed_issues_with_label(repo_full_name):
    """Gets closed issues with a 'bounty' label for a specific repo."""
    owner, repo = repo_full_name.split('/')
    print(f"Fetching closed issues for repo: {repo_full_name}")
    # Fetch closed issues, filtering by state=closed server-side
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=closed"
    issues = get_paginated_data(url)
    print(f"Found {len(issues)} closed issues in {repo_full_name}. Filtering for bounty labels...")

    bounty_issues = []
    for issue in issues:
        # Ignore pull requests that might appear in the issues list
        if 'pull_request' in issue:
            continue

        # Use the main system's logic to identify bounty issues
        title = issue.get('title', '')
        labels = issue.get('labels', [])
        if is_bounty_issue(title, labels):
            bounty_issues.append(issue)

    print(f"Found {len(bounty_issues)} closed issues with bounty labels in {repo_full_name}.")
    return bounty_issues

def format_historical_issue(issue):
    """Formats a GitHub issue into the structure needed for the table."""
    closed_at_str = issue.get("closed_at")
    last_updated_date = "N/A"
    if closed_at_str:
        try:
            last_updated_date = datetime.datetime.fromisoformat(closed_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
        except ValueError:
            print(f"Warning: Could not parse closed_at date: {closed_at_str}")

    # Try to get assignee, fallback to N/A
    assignee = issue.get("assignee")
    contributor = assignee.get("login") if assignee else "Unknown"
    # Extract value/currency first from labels, then from title/body
    labels = issue.get("labels", [])
    extracted_value, extracted_currency = extract_from_labels(labels)

    if not extracted_value or not extracted_currency:
        title = issue.get("title", "")
        body = issue.get("body", "") # Body might be None, handle gracefully
        extracted_value, extracted_currency = extract_from_text(title, body if body else "")

    return {
        # "contributor": contributor, # Removed as requested
        "work_title_text": issue.get("title", "N/A"),
        "value": extracted_value if extracted_value else "Unknown",
        "currency": extracted_currency if extracted_currency else "",
        # "wallet": "N/A", # Removed as requested
        "reviewer": issue.get("user", {}).get("login", "Unknown"), # Original issue reporter
        "work_link": issue.get("html_url", "#"),
        "_last_modified_date": last_updated_date,
        "_filename": None # Not applicable for historical issues
    }

# --- Markdown Generation (Copied and adapted from payment_status_generator.py) ---

def truncate_address(address, start_len=4, end_len=3):
    """Truncates a string address, showing start and end parts."""
    if not isinstance(address, str) or len(address) <= start_len + end_len + 3:
        return address
    return f"{address[:start_len]}...{address[-end_len:]}"

def format_value(value, currency):
    """Formats the bounty value and currency."""
    if value == "Unknown":
        return value
    try:
        val_str = f"{float(value):.2f}"
    except (ValueError, TypeError):
        val_str = str(value)
    return f"{val_str} {currency}" if currency else val_str

def generate_markdown_table(submissions):
    """Generates a Markdown table for a list of submissions (adapted for historical)."""
    if not submissions:
        return "No closed bounties found.\n" # Updated message

    # Remove Contributor and Wallet Address headers
    headers = ["Work Title", "Value", "Reviewer", "Work Link", "Closed Date"]
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    # Sort by closed date descending (most recent first)
    for sub in sorted(submissions, key=lambda x: x.get('_last_modified_date', '0000-00-00'), reverse=True):
        # contributor = sub.get("contributor", "N/A") # Removed
        work_title_text = sub.get("work_title_text", "N/A")
        value = sub.get("value", "Unknown")
        currency = sub.get("currency", "")
        # wallet = sub.get("wallet", "N/A") # Removed
        reviewer = sub.get("reviewer", "N/A")
        work_link = sub.get("work_link", "#")
        work_link_md = f"[Issue]({work_link})" if work_link and work_link != "#" else "N/A"
        # Link title to issue URL
        linked_work_title = f"[{work_title_text}]({work_link})" if work_link and work_link != "#" else work_title_text
        last_modified_date = sub.get("_last_modified_date", "N/A")
        value_str = format_value(value, currency)

        # Adjust row content to match new headers
        row = [
            linked_work_title,
            value_str,
            reviewer,
            work_link_md,
            last_modified_date
        ]
        table += "| " + " | ".join(map(str, row)) + " |\n"

    return table

def get_existing_issue_links(filepath):
    """Parses an existing markdown file to extract issue links from tables."""
    links = set()
    if not filepath.exists():
        return links
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Simple regex to find markdown links in table rows, specifically targeting issue links
        # Looks for [Issue](URL) or [Title](URL) patterns within table rows (| .... |)
        link_pattern = re.compile(r"\|.*\[(?:Issue|[^\]]+)\]\((https://github\.com/[\w.-]+/[\w.-]+/(?:issues|pull)/\d+)\).*\|")
        for line in content.splitlines():
            if line.strip().startswith('|') and '---' not in line:
                 match = link_pattern.search(line)
                 if match:
                     links.add(match.group(1))
    except Exception as e:
        print(f"Warning: Could not parse existing file {filepath} for links: {e}")
    print(f"Found {len(links)} existing issue links in {filepath}.")
    return links

# --- Main Execution ---

def main():
    """Main function to fetch historical issues and append to paid.md."""
    print("Starting historical paid bounty backfill...")
    if not TOKEN:
        print("Error: GITHUB_TOKEN or PAT_TOKEN environment variable not set.")
        return

    # --- Load Repositories ---
    repos_to_scan = set()
    try:
        # Load individual repos
        if TRACKED_REPOS_FILE.exists():
            with open(TRACKED_REPOS_FILE, 'r', encoding='utf-8') as f:
                repo_list = json.load(f)
                # Ensure it's a list of objects with 'owner' and 'repo'
                if isinstance(repo_list, list):
                    for repo_info in repo_list:
                        if isinstance(repo_info, dict) and "owner" in repo_info and "repo" in repo_info:
                             repos_to_scan.add(f"{repo_info['owner']}/{repo_info['repo']}")
                        else:
                             print(f"Warning: Skipping invalid entry in {TRACKED_REPOS_FILE}: {repo_info}")
                else:
                    print(f"Warning: Expected a list in {TRACKED_REPOS_FILE}, but found {type(repo_list)}. Skipping.")

        # Load orgs and fetch their repos
        if TRACKED_ORGS_FILE.exists():
            with open(TRACKED_ORGS_FILE, 'r', encoding='utf-8') as f:
                org_list = json.load(f)
                 # Ensure it's a list of objects with 'org'
                if isinstance(org_list, list):
                    for org_info in org_list:
                         if isinstance(org_info, dict) and "org" in org_info:
                             org_name = org_info["org"]
                             repos_to_scan.update(get_org_repos(org_name))
                             time.sleep(API_DELAY_SECONDS) # Delay between orgs
                         else:
                             print(f"Warning: Skipping invalid entry in {TRACKED_ORGS_FILE}: {org_info}")
                else:
                     print(f"Warning: Expected a list in {TRACKED_ORGS_FILE}, but found {type(org_list)}. Skipping.")
    except Exception as e:
        print(f"Error loading repository configuration: {e}")
        return

    if not repos_to_scan:
        print("Error: No repositories found to scan.")
        return

    print(f"\nScanning {len(repos_to_scan)} repositories...")

    # --- Fetch and Filter Issues ---
    all_historical_issues = []
    for repo_name in sorted(list(repos_to_scan)): # Sort for consistent processing order
        all_historical_issues.extend(get_closed_issues_with_label(repo_name))
        time.sleep(API_DELAY_SECONDS) # Delay between repos

    print(f"\nFound {len(all_historical_issues)} total closed issues with bounty labels across all scanned repos.")

    # --- Format Issues ---
    # No need to filter duplicates here anymore, as we replace the whole section
    formatted_issues = [format_historical_issue(issue) for issue in all_historical_issues]
    print(f"Formatted {len(formatted_issues)} historical issues.")

    if not formatted_issues:
        print("No historical issues found to add/update.")
        # Optionally, ensure the historical section is removed if it exists but no issues are found
        # (Code below handles this by writing only existing_content if historical_table is empty)
        # return # Or proceed to potentially clear the section

    # --- Generate Markdown Table ---
    # Pass all formatted issues, the writing logic handles replacement
    historical_table = generate_markdown_table(formatted_issues)
    # historical_content = f"\n{HISTORICAL_HEADER_NEW}\n\n{historical_table}\n" # Moved generation lower down

    try:
        # Read existing content and append, or create new file
        existing_content = ""
        if OUTPUT_FILE.exists():
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            # Find the start of the historical section
            historical_section_start = existing_content.find(HISTORICAL_HEADER)

            if historical_section_start != -1:
                print(f"Replacing existing '{HISTORICAL_HEADER}' section in {OUTPUT_FILE}.")
                # Keep only the content *before* the historical section
                existing_content = existing_content[:historical_section_start].strip()
            else:
                # If header not found, just strip whitespace from existing content
                print(f"No existing '{HISTORICAL_HEADER}' section header found in {OUTPUT_FILE}. Appending new section.")
                existing_content = existing_content.strip()

        # Ensure directory exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Generate the final content with the correct header only if there's a table to write
        final_historical_content = ""
        if historical_table and "No closed bounties found" not in historical_table:
             final_historical_content = f"\n{HISTORICAL_HEADER}\n\n{historical_table}\n" # Use simplified header variable
        else:
             print("No valid historical table generated.")


        # Write the file, overwriting or creating as needed
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            if existing_content: # Write existing content (before historical section) if it's not empty
                 f.write(existing_content)
                 if final_historical_content: # Add spacing only if adding the historical section
                      f.write("\n\n")
            if final_historical_content:
                 f.write(final_historical_content) # Write the new/updated historical section
            elif not existing_content: # Handle case where file was only historical section
                 f.write("# Paid Bounties\n\nThis page lists completed and paid bounty submissions.\n\nNo submissions found for these statuses.\n") # Write default empty content

        print(f"Successfully updated historical issues section in {OUTPUT_FILE}") # Clarified message

        # --- Generate and Append Statistics ---
        # Use the originally fetched issues (all_historical_issues) for stats calculation
        if all_historical_issues: # Check if we fetched any issues at all
            print("Generating statistics...")
            stats_content = generate_stats_markdown(all_historical_issues)
            if stats_content:
                 with open(OUTPUT_FILE, 'a', encoding='utf-8') as f: # Append stats
                      f.write("\n\n" + stats_content)
                 print(f"Successfully appended statistics to {OUTPUT_FILE}")
            else:
                 print("No statistics generated.")
        else:
            print("Skipping statistics generation as no historical issues were found.")

    except Exception as e:
        print(f"Error writing final output file {OUTPUT_FILE}: {e}")

# --- Statistics Generation ---

def generate_stats_markdown(issues):
    """Generates markdown tables for statistics based on the fetched issues."""
    if not issues:
        return ""

    stats_md = "\n---\n\n## Historical Statistics\n\n"

    # Top Repos by Closed Bounty Count
    repo_counts = Counter()
    for issue in issues:
        repo_match = re.search(r"github\.com/([\w.-]+/[\w.-]+)/issues/\d+", issue.get("html_url", ""))
        if repo_match:
            repo_counts[repo_match.group(1)] += 1

    stats_md += "### Top 5 Repositories by Closed Bounties\n\n"
    if repo_counts:
        stats_md += "| Repository | Count |\n"
        stats_md += "|---|---|\n"
        for repo, count in repo_counts.most_common(5):
            stats_md += f"| {repo} | {count} |\n"
    else:
        stats_md += "No repository data found.\n"
    stats_md += "\n"


    # Top Issue Creators (Reviewers in our context) by Closed Bounty Count
    creator_counts = Counter()
    for issue in issues:
        creator = issue.get("user", {}).get("login")
        if creator:
            creator_counts[creator] += 1

    stats_md += "### Top 5 Issue Creators by Closed Bounties\n\n"
    if creator_counts:
        stats_md += "| Creator (Reviewer) | Count |\n"
        stats_md += "|---|---|\n"
        for creator, count in creator_counts.most_common(5):
            stats_md += f"| {creator} | {count} |\n"
    else:
        stats_md += "No creator data found.\n"
    stats_md += "\n"

    # Add more stats here if needed

    return stats_md


if __name__ == "__main__":
    main()
