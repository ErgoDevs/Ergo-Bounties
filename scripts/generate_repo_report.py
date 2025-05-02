import os
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone # Changed import
from operator import itemgetter

# Add project root to sys.path to allow importing 'src' if needed later
# (Though not strictly needed for this script's current imports)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# --- Configuration ---
load_dotenv()
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("PAT_TOKEN")
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
API_DELAY_SECONDS = 0.5
REPOS_PER_PAGE = 100

CONFIG_DIR = Path("src/config")
TRACKED_ORGS_FILE = CONFIG_DIR / "tracked_orgs.json"
TRACKED_REPOS_FILE = CONFIG_DIR / "tracked_repos.json"
OUTPUT_FILE = Path("data/repos.md")
ALL_REPOS_FILE = Path("data/all_repos.json") # Input file for all repos

# --- Helper Functions ---

def format_relative_date(dt_object):
    """Formats a datetime object into a relative time string."""
    if not dt_object:
        return "N/A"
    now = datetime.now(timezone.utc)
    diff = now - dt_object

    seconds = diff.total_seconds()
    days = diff.days

    if days >= 365:
        years = days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    if days >= 30:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    if days >= 7:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    if days >= 1:
        return f"{days} day{'s' if days > 1 else ''} ago"
    if seconds >= 3600:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if seconds >= 60:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    return "just now"


def get_paginated_data(url):
    """Fetches all pages of data from a GitHub API endpoint."""
    results = []
    separator = '&' if '?' in url else '?'
    page_url = f"{url}{separator}per_page={REPOS_PER_PAGE}"
    while page_url:
        try:
            print(f"Fetching: {page_url}")
            response = requests.get(page_url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                results.extend(data)
            else:
                results.append(data)
                break
            page_url = response.links.get("next", {}).get("url")
            if page_url:
                time.sleep(API_DELAY_SECONDS)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching paginated data from {page_url}: {e}")
            if response is not None and response.status_code == 403:
                 print("Rate limit likely exceeded or token permissions issue.")
            break
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

def get_repo_details(repo_full_name):
    """Fetches details for a single repository."""
    owner, repo = repo_full_name.split('/')
    url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        print(f"Fetching details for repo: {repo_full_name}")
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        # Extract relevant details
        pushed_at_str = data.get("pushed_at")
        last_push_dt = None # Store as datetime object
        if pushed_at_str:
            try:
                # Parse ISO string, ensuring it's timezone-aware (UTC)
                last_push_dt = datetime.fromisoformat(pushed_at_str.replace('Z', '+00:00'))
            except ValueError:
                print(f"Warning: Could not parse pushed_at date: {pushed_at_str}")

        return {
            "owner": owner, # Add owner
            "full_name": repo_full_name,
            "html_url": data.get("html_url", "#"),
            "description": data.get("description", "") or "", # Ensure empty string if None
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "last_push_dt": last_push_dt, # Use datetime object
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for {repo_full_name}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching details for {repo_full_name}: {e}")
        return None

# --- Markdown Generation ---

def generate_repos_markdown(repo_details_list):
    """Generates the markdown content with separate tables for each organization."""
    if not repo_details_list:
        return "No repository details found.\n"

    # Group repositories by owner
    repos_by_org = {}
    for repo in repo_details_list:
        owner = repo['owner']
        if owner not in repos_by_org:
            repos_by_org[owner] = []
        repos_by_org[owner].append(repo)

    # --- Generate Organization Summary Table ---
    org_summary_content = "## 🏢 Organizations\n\n"
    org_summary_content += "This table summarizes the organizations with tracked repositories in the Ergo ecosystem.\n\n"
    org_summary_content += "| Organization | Tracked Repositories |\n"
    org_summary_content += "|---|---|\n"

    # Sort orgs by name for the summary table
    for org_name in sorted(repos_by_org.keys()):
        org_link = f"[{org_name}](https://github.com/{org_name})"
        repo_count = len(repos_by_org[org_name])
        org_summary_content += f"| {org_link} | {repo_count} |\n"
    org_summary_content += "\n"

    # --- Generate Repository Tables per Organization ---
    repo_tables_content = "##  repositories\n\n"
    repo_tables_content += "Repositories are grouped by organization and sorted by star count within each group.\n\n"

    # Sort organizations by name for consistent output order
    for org_name in sorted(repos_by_org.keys()):
        org_repos = repos_by_org[org_name]
        # Sort repos within the org by stars descending
        sorted_org_repos = sorted(org_repos, key=itemgetter('stars'), reverse=True)

        org_link = f"https://github.com/{org_name}"
        repo_tables_content += f"### [{org_name}]({org_link}) ({len(sorted_org_repos)} Repos)\n\n"

        headers = ["Repository", "⭐ Stars", "🍴 Forks", "🐛 Open Issues", "📅 Last Push", "📝 Description"]
        repo_tables_content += "| " + " | ".join(headers) + " |\n"
        repo_tables_content += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        for repo in sorted_org_repos:
            repo_link = f"[{repo['full_name'].split('/')[1]}]({repo['html_url']})" # Show only repo name in link
            # Truncate description
            description = repo['description'] if repo['description'] else "" # Handle None
            if len(description) > 80: # Slightly shorter truncation
                description = description[:77] + "..."
            # Replace pipes
            description = description.replace("|", "\\|").replace("\r", "").replace("\n", " ") # Also remove newlines

            relative_date = format_relative_date(repo['last_push_dt'])

            row = [
                repo_link,
                str(repo['stars']),
                str(repo['forks']),
                str(repo['open_issues']),
                relative_date,
                description
            ]
            repo_tables_content += "| " + " | ".join(row) + " |\n"
        repo_tables_content += "\n" # Add space between org tables

    return org_summary_content + repo_tables_content


def generate_all_repos_markdown(repo_details_list):
    """Generates the markdown table for all repositories, sorted by last push."""
    if not repo_details_list:
        return "No additional repository details found.\n"

    # Sort by last push date descending (newest first), handle None values
    sorted_repos = sorted(
        repo_details_list,
        key=lambda x: x['last_push_dt'] if x['last_push_dt'] else datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )

    content = "## 🌐 All Ergo-Related Repositories (including untracked)\n\n"
    content += "This list includes repositories from `data/all_repos.json`, sorted by the most recent activity.\n\n"

    headers = ["Repository", "Owner", "📅 Last Push", "⭐ Stars", "📝 Description"]
    content += "| " + " | ".join(headers) + " |\n"
    content += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for repo in sorted_repos:
        repo_link = f"[{repo['full_name'].split('/')[1]}]({repo['html_url']})"
        owner_link = f"[{repo['owner']}](https://github.com/{repo['owner']})"
        # Truncate description
        description = repo['description'] if repo['description'] else ""
        if len(description) > 80:
            description = description[:77] + "..."
        # Replace pipes and newlines
        description = description.replace("|", "\\|").replace("\r", "").replace("\n", " ")

        relative_date = format_relative_date(repo['last_push_dt'])

        row = [
            repo_link,
            owner_link,
            relative_date,
            str(repo['stars']),
            description
        ]
        content += "| " + " | ".join(row) + " |\n"

    return content + "\n"

# --- Main Execution ---

def main():
    """Main function to load repos, fetch details, and generate the report."""
    print("Starting repository report generation...")
    if not TOKEN:
        print("Error: GITHUB_TOKEN or PAT_TOKEN environment variable not set.")
        return

    # --- Load Tracked Repositories ---
    tracked_repos_to_scan = set()
    try:
        if TRACKED_REPOS_FILE.exists():
            with open(TRACKED_REPOS_FILE, 'r', encoding='utf-8') as f:
                repo_list = json.load(f)
                if isinstance(repo_list, list):
                    for repo_info in repo_list:
                        if isinstance(repo_info, dict) and "owner" in repo_info and "repo" in repo_info:
                             tracked_repos_to_scan.add(f"{repo_info['owner']}/{repo_info['repo']}")
                        else:
                             print(f"Warning: Skipping invalid entry in {TRACKED_REPOS_FILE}: {repo_info}")
                else:
                    print(f"Warning: Expected a list in {TRACKED_REPOS_FILE}, but found {type(repo_list)}. Skipping.")

        if TRACKED_ORGS_FILE.exists():
            with open(TRACKED_ORGS_FILE, 'r', encoding='utf-8') as f:
                org_list = json.load(f)
                if isinstance(org_list, list): # Corrected indentation
                    for org_info in org_list:
                        if isinstance(org_info, dict) and "org" in org_info: # Corrected indentation
                            org_name = org_info["org"]
                            tracked_repos_to_scan.update(get_org_repos(org_name))
                            time.sleep(API_DELAY_SECONDS)
                        else: # Corrected indentation
                            print(f"Warning: Skipping invalid entry in {TRACKED_ORGS_FILE}: {org_info}") # Corrected indentation
                else: # Corrected indentation
                    print(f"Warning: Expected a list in {TRACKED_ORGS_FILE}, but found {type(org_list)}. Skipping.") # Corrected indentation
    except Exception as e:
        print(f"Error loading tracked repository configuration: {e}")
        # Continue even if tracked repos fail, might still load all_repos

    if not tracked_repos_to_scan:
        print("Warning: No tracked repositories found to scan.")
        # Continue to try and load all_repos

    print(f"\nFound {len(tracked_repos_to_scan)} unique tracked repositories to fetch details for...")

    # --- Fetch Tracked Repository Details ---
    tracked_repo_details = []
    for repo_name in sorted(list(tracked_repos_to_scan)):
        details = get_repo_details(repo_name)
        if details:
            tracked_repo_details.append(details)
        time.sleep(API_DELAY_SECONDS) # Delay between repo detail fetches

    print(f"\nSuccessfully fetched details for {len(tracked_repo_details)} tracked repositories.")

    # --- Load and Fetch All Repositories (from all_repos.json) ---
    all_repos_urls = []
    if ALL_REPOS_FILE.exists():
        try:
            with open(ALL_REPOS_FILE, 'r', encoding='utf-8') as f:
                all_repos_urls = json.load(f)
            print(f"Loaded {len(all_repos_urls)} URLs from {ALL_REPOS_FILE}")
        except Exception as e:
            print(f"Error loading {ALL_REPOS_FILE}: {e}")
            all_repos_urls = []
    else:
        print(f"Warning: {ALL_REPOS_FILE} not found.")

    all_repo_names_to_fetch = set()
    for url in all_repos_urls:
        if isinstance(url, str) and url.startswith("https://github.com/"):
            parts = url.strip('/').split('/')
            # Check if it's a repo URL (e.g., https://github.com/owner/repo)
            if len(parts) == 5:
                repo_name = f"{parts[3]}/{parts[4]}"
                # Add only if it wasn't already tracked
                if repo_name not in tracked_repos_to_scan:
                    all_repo_names_to_fetch.add(repo_name)
            # Ignore org URLs (e.g., https://github.com/owner) or other formats

    print(f"Found {len(all_repo_names_to_fetch)} additional unique repositories from {ALL_REPOS_FILE} to fetch.")

    all_repo_details_untracked = []
    for repo_name in sorted(list(all_repo_names_to_fetch)):
        details = get_repo_details(repo_name)
        if details:
            all_repo_details_untracked.append(details)
        time.sleep(API_DELAY_SECONDS)

    print(f"Successfully fetched details for {len(all_repo_details_untracked)} additional repositories.")

    # Combine tracked and untracked details for the "all repos" section
    combined_all_repo_details = tracked_repo_details + all_repo_details_untracked

    # --- Generate and Write Markdown ---
    markdown_content = "# 🏗️ Ergo Ecosystem Repositories Overview\n\n"
    markdown_content += "This page provides an overview of GitHub organizations and repositories actively building on or supporting the Ergo ecosystem.\n\n"
    markdown_content += "## Tracked Repositories\n\n"
    markdown_content += "Repositories listed here are actively tracked for bounties via `src/config/tracked_repos.json` and `src/config/tracked_orgs.json`.\n\n"
    markdown_content += "*Note: Standard Markdown tables do not support interactive sorting or toggling. The tables below are static.*\n\n"
    markdown_content += generate_repos_markdown(tracked_repo_details) # Generate summary and tables for TRACKED repos
    markdown_content += "\n---\n\n" # Separator
    markdown_content += generate_all_repos_markdown(combined_all_repo_details) # Generate table for ALL repos (tracked + untracked from json)

    try:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Successfully generated repository report at {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing output file {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    main()
