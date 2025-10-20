import os
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta # Added timedelta
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
ENTITIES_TO_SCAN_FILE = CONFIG_DIR / "entities_to_scan.json" # New consolidated config
TRACKED_REPOS_FILE = CONFIG_DIR / "tracked_repos.json" # Still needed for individual tracked repos
TRACKED_REPOS_OUTPUT_FILE = Path("data/tracked_repos.md") # Output for tracked repos
ALL_REPOS_OUTPUT_FILE = Path("data/all_repos.md")     # Output for all repos
ALL_REPOS_INPUT_FILE = Path("data/all_repos.json")   # Input file for individual non-org/non-tracked repos
# ALL_ORGS_INPUT_FILE is no longer needed, replaced by ENTITIES_TO_SCAN_FILE

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
    print(f"Found {len(repo_names)} repositories for organization: {org_name}.")
    return repo_names

def get_user_repos(username):
    """Gets all repositories for a given user."""
    print(f"Fetching repositories for user: {username}")
    url = f"https://api.github.com/users/{username}/repos"
    repos = get_paginated_data(url)
    # Filter out forks if desired, or keep all
    repo_names = [f"{username}/{repo['name']}" for repo in repos if repo.get('name')] # and not repo.get('fork')]
    print(f"Found {len(repo_names)} repositories for user: {username}.")
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


def get_repo_activity_last_month(repo_full_name):
    """Fetches commit count and unique contributors for the last 30 days."""
    print(f"Fetching activity for {repo_full_name}...")
    owner, repo = repo_full_name.split('/')
    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    since_date_str = one_month_ago.isoformat()

    commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?since={since_date_str}&per_page=100"

    commit_count = 0
    contributors = set()
    page_url = commits_url

    while page_url:
        response = None # Initialize response to None before the try block
        try:
            # print(f"Fetching commits page: {page_url}") # Optional: verbose logging
            response = requests.get(page_url, headers=HEADERS)
            # Handle 404 specifically - repo might be gone or private
            if response.status_code == 404:
                print(f"Warning: Repo {repo_full_name} not found or inaccessible (404). Skipping activity check.")
                break
            # Handle other errors
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                 print(f"Warning: Unexpected commit data format for {repo_full_name}. Skipping.")
                 break # Stop processing this repo if data format is wrong

            commit_count += len(data)
            for commit in data:
                # Try to get login from author field first, fallback to committer if author is null
                if commit.get('author') and commit['author'].get('login'):
                    contributors.add(commit['author']['login'])
                elif commit.get('committer') and commit['committer'].get('login'):
                     # Less ideal, but better than nothing if author is null
                     contributors.add(commit['committer']['login'])
                # Handle cases where commit info might be incomplete (e.g., null author/committer)

            page_url = response.links.get("next", {}).get("url")
            if page_url:
                time.sleep(API_DELAY_SECONDS / 2) # Slightly shorter delay for pagination within a repo

        except requests.exceptions.RequestException as e:
            print(f"Error fetching commits for {repo_full_name} from {page_url}: {e}")
            if response is not None and response.status_code == 403:
                 print("Rate limit likely exceeded or token permissions issue.")
            # Stop processing this repo on error to avoid hammering API
            break
        except Exception as e:
            print(f"Unexpected error processing commits for {repo_full_name}: {e}")
            break # Stop processing this repo on unexpected error

    print(f" -> Found {commit_count} commits, {len(contributors)} contributors for {repo_full_name} in last 30 days.")
    return {'commit_count': commit_count, 'contributors': contributors}


def generate_stats_markdown(total_repos, total_entities, updated_last_month, commits_last_month, unique_contributors_last_month):
    """Generates the markdown section for the stats."""
    stats_content = "## 📊 Ecosystem Activity Overview (Last 30 Days)\n\n"
    stats_content += f"- **Total Repositories Listed:** {total_repos}\n"
    stats_content += f"- **Total Organizations/Users Scanned:** {total_entities}\n"
    stats_content += f"- **Repositories Updated:** {updated_last_month}\n"
    stats_content += f"- **Commits Made:** {commits_last_month}\n"
    stats_content += f"- **Unique Contributors:** {unique_contributors_last_month}\n\n"
    stats_content += "---\n\n" # Add a separator
    return stats_content

# --- Main Execution ---

def main():
    """Main function to load repos, fetch details, and generate the report."""
    print("Starting repository report generation...")
    if not TOKEN:
        print("Error: GITHUB_TOKEN or PAT_TOKEN environment variable not set.")
        return

    # --- Load Entities and Repos to Scan ---
    all_entities = []
    if ENTITIES_TO_SCAN_FILE.exists():
        try:
            with open(ENTITIES_TO_SCAN_FILE, 'r', encoding='utf-8') as f:
                all_entities = json.load(f)
            print(f"Loaded {len(all_entities)} entities from {ENTITIES_TO_SCAN_FILE}")
        except Exception as e:
            print(f"Error loading {ENTITIES_TO_SCAN_FILE}: {e}")
            # Potentially exit or continue with empty list depending on desired behavior
            return # Exit if main config is broken

    tracked_repos_to_scan = set() # Repos from entities marked tracked_for_bounties: true
    all_repos_to_scan = set()     # Repos from ALL entities + individual files
    entity_names = set(entity['name'] for entity in all_entities if isinstance(entity, dict) and 'name' in entity) # For filtering individual repos

    # Process entities from the new config file
    for entity_info in all_entities:
        if isinstance(entity_info, dict) and "name" in entity_info and "type" in entity_info and "tracked_for_bounties" in entity_info:
            name = entity_info["name"]
            entity_type = entity_info["type"]
            is_tracked = entity_info["tracked_for_bounties"]
            repos_found = set()

            if entity_type == "org":
                repos_found = get_org_repos(name)
            elif entity_type == "user":
                repos_found = get_user_repos(name)
            else:
                print(f"Warning: Skipping entry with unknown type in {ENTITIES_TO_SCAN_FILE}: {entity_info}")
                continue # Skip to next entity

            all_repos_to_scan.update(repos_found)
            if is_tracked:
                tracked_repos_to_scan.update(repos_found)
            time.sleep(API_DELAY_SECONDS)
        else:
            print(f"Warning: Skipping invalid entry in {ENTITIES_TO_SCAN_FILE}: {entity_info}")

    # Add individually tracked repos (from old tracked_repos.json)
    if TRACKED_REPOS_FILE.exists():
         try:
            with open(TRACKED_REPOS_FILE, 'r', encoding='utf-8') as f:
                individual_tracked_repos = json.load(f)
            if isinstance(individual_tracked_repos, list):
                 for repo_info in individual_tracked_repos:
                     if isinstance(repo_info, dict) and "owner" in repo_info and "repo" in repo_info:
                         repo_name = f"{repo_info['owner']}/{repo_info['repo']}"
                         tracked_repos_to_scan.add(repo_name)
                         all_repos_to_scan.add(repo_name) # Ensure it's also in the 'all' list
                     else:
                         print(f"Warning: Skipping invalid entry in {TRACKED_REPOS_FILE}: {repo_info}")
            else:
                 print(f"Warning: Expected a list in {TRACKED_REPOS_FILE}, but found {type(individual_tracked_repos)}. Skipping.")
         except Exception as e:
             print(f"Error loading or processing {TRACKED_REPOS_FILE}: {e}")

    # Add individual non-tracked repos (from all_repos.json), filtering out those whose owner is an entity
    if ALL_REPOS_INPUT_FILE.exists():
        try:
            with open(ALL_REPOS_INPUT_FILE, 'r', encoding='utf-8') as f:
                individual_repo_urls = json.load(f)
            print(f"Processing {len(individual_repo_urls)} individual repo URLs from {ALL_REPOS_INPUT_FILE}")
            for url in individual_repo_urls:
                 if isinstance(url, str) and url.startswith("https://github.com/"):
                    parts = url.strip('/').split('/')
                    if len(parts) == 5: # It's a repo URL
                        owner = parts[3]
                        repo = parts[4]
                        repo_full_name = f"{owner}/{repo}"
                        # Add only if owner is NOT an entity we already processed
                        if owner not in entity_names:
                            all_repos_to_scan.add(repo_full_name)
        except Exception as e:
            print(f"Error loading or processing {ALL_REPOS_INPUT_FILE}: {e}")
    else:
        print(f"Warning: {ALL_REPOS_INPUT_FILE} not found.")


    print(f"\nTotal unique repositories identified for 'all_repos.md': {len(all_repos_to_scan)}")
    print(f"Total unique repositories identified for 'tracked_repos.md': {len(tracked_repos_to_scan)}")

    # --- Fetch Details ---
    # Fetch details only for repos marked as tracked
    print(f"\nFetching details for {len(tracked_repos_to_scan)} tracked repositories...")
    tracked_repo_details = []
    fetched_details_repo_names = set() # Keep track of what we've fetched

    for repo_name in sorted(list(tracked_repos_to_scan)):
        details = get_repo_details(repo_name)
        if details:
            tracked_repo_details.append(details)
            fetched_details_repo_names.add(repo_name)
        time.sleep(API_DELAY_SECONDS)
    print(f"Successfully fetched details for {len(tracked_repo_details)} tracked repositories.")

    # Determine which additional details are needed for the 'all' list
    additional_repos_to_fetch = all_repos_to_scan - fetched_details_repo_names
    print(f"\nFetching details for {len(additional_repos_to_fetch)} additional repositories for 'all_repos.md'...")
    all_repo_details_additional = []
    for repo_name in sorted(list(additional_repos_to_fetch)):
        details = get_repo_details(repo_name)
        if details:
            all_repo_details_additional.append(details)
            # No need to add to fetched_details_repo_names here, already done implicitly
        time.sleep(API_DELAY_SECONDS)
    print(f"Successfully fetched details for {len(all_repo_details_additional)} additional repositories.")

    # 5. Combine tracked repo details with the newly fetched details for the "all repos" file
    combined_all_repo_details = tracked_repo_details + all_repo_details_additional

    # --- Calculate Activity Stats (Last 30 Days) ---
    print("\nCalculating activity stats for the last 30 days...")
    total_commits_last_month = 0
    all_contributors_last_month = set()
    repos_updated_last_month = 0
    one_month_ago_dt = datetime.now(timezone.utc) - timedelta(days=30)

    # Iterate over the combined list to calculate stats
    for repo_detail in combined_all_repo_details:
        # Check if updated recently
        if repo_detail['last_push_dt'] and repo_detail['last_push_dt'] >= one_month_ago_dt:
            repos_updated_last_month += 1

        # Fetch commit activity
        activity = get_repo_activity_last_month(repo_detail['full_name'])
        total_commits_last_month += activity['commit_count']
        all_contributors_last_month.update(activity['contributors'])
        time.sleep(API_DELAY_SECONDS) # Delay between repos for activity check

    unique_contributors_last_month = len(all_contributors_last_month)
    print(f"\nStats Calculation Complete:")
    print(f" - Repos Updated: {repos_updated_last_month}")
    print(f" - Commits: {total_commits_last_month}")
    print(f" - Unique Contributors: {unique_contributors_last_month}")

    # --- Generate and Write Tracked Repos Markdown ---
    tracked_markdown_content = "# 🏗️ Tracked Ergo Ecosystem Repositories\n\n"
    tracked_markdown_content += "This page provides an overview of GitHub organizations and repositories actively tracked for bounties via `src/config/tracked_repos.json` and `src/config/tracked_orgs.json`.\n\n"
    # Removed the note about markdown limitations
    tracked_markdown_content += generate_repos_markdown(tracked_repo_details) # Generate summary and tables for TRACKED repos
    tracked_markdown_content += "\n---\n\n"
    tracked_markdown_content += "[View All Ergo-Related Repositories (including untracked) →](all_repos.md)\n"

    try:
        TRACKED_REPOS_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True) # Use correct output variable
        with open(TRACKED_REPOS_OUTPUT_FILE, 'w', encoding='utf-8') as f: # Use correct output variable
            f.write(tracked_markdown_content)
        print(f"Successfully generated tracked repository report at {TRACKED_REPOS_OUTPUT_FILE}") # Use correct output variable
    except Exception as e:
        print(f"Error writing output file {TRACKED_REPOS_OUTPUT_FILE}: {e}") # Use correct output variable

    # --- Generate and Write All Repos Markdown ---
    stats_section = generate_stats_markdown(
        total_repos=len(combined_all_repo_details),
        total_entities=len(all_entities),
        updated_last_month=repos_updated_last_month,
        commits_last_month=total_commits_last_month,
        unique_contributors_last_month=unique_contributors_last_month
    )
    all_repos_markdown_content = "#  All Ergo-Related Repositories\n\n"
    all_repos_markdown_content += "[View Tracked Repositories Only →](tracked_repos.md)\n\n" # Add link back
    all_repos_markdown_content += stats_section # Prepend the stats section
    # The generate_all_repos_markdown function already adds the H2 title for the table
    all_repos_markdown_content += generate_all_repos_markdown(combined_all_repo_details) # Generate table for ALL repos

    try:
        ALL_REPOS_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True) # Use correct output variable
        with open(ALL_REPOS_OUTPUT_FILE, 'w', encoding='utf-8') as f: # Use correct output variable
            f.write(all_repos_markdown_content)
        print(f"Successfully generated all repositories report at {ALL_REPOS_OUTPUT_FILE}") # Use correct output variable
    except Exception as e:
        print(f"Error writing output file {ALL_REPOS_OUTPUT_FILE}: {e}") # Use correct output variable

if __name__ == "__main__":
    main()
