import os
import json
from collections import defaultdict
from pathlib import Path

SUBMISSIONS_DIR = Path("submissions")
ACTIVE_STATUS_FILE = Path("data/payment_status.md")
PAID_STATUS_FILE = Path("data/paid.md")
# Define the new valid statuses and their order for the active report
ACTIVE_STATUS_ORDER = ["awaiting-review", "reviewed", "in-progress"]
PAID_STATUS = "paid"
VALID_STATUSES = set(ACTIVE_STATUS_ORDER + [PAID_STATUS]) # Used for potential future validation if needed
IGNORE_FILES = {"example-user-ergoscript-fsmtest.json"} # Files to ignore

def load_submissions():
    """Loads all submission JSON files from the submissions directory."""
    submissions = []
    if not SUBMISSIONS_DIR.is_dir():
        print(f"Error: Submissions directory not found at {SUBMISSIONS_DIR}")
        return submissions

    for filename in SUBMISSIONS_DIR.glob("*.json"):
        if filename.name in IGNORE_FILES:
            print(f"Ignoring file: {filename.name}")
            continue
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Add filename for reference if needed later
                data['_filename'] = filename.name
                submissions.append(data)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {filename}")
        except Exception as e:
            print(f"Warning: Error reading {filename}: {e}")
    return submissions

def group_by_status(submissions):
    """Groups submissions by their status."""
    grouped = defaultdict(list)
    for sub in submissions:
        status = sub.get("status", "unknown").lower()
        grouped[status].append(sub)
    return grouped

def format_value(value, currency):
    """Formats the bounty value and currency."""
    try:
        # Attempt to format as float with 2 decimal places if possible
        val_str = f"{float(value):.2f}"
    except (ValueError, TypeError):
        val_str = str(value) # Fallback to string representation
    return f"{val_str} {currency}" if currency else val_str

def truncate_address(address, start_len=4, end_len=3):
    """Truncates a string address, showing start and end parts."""
    if not isinstance(address, str) or len(address) <= start_len + end_len + 3: # +3 for "..."
        return address # Return original if too short or not a string
    return f"{address[:start_len]}...{address[-end_len:]}"

def generate_markdown_table(submissions):
    """Generates a Markdown table for a list of submissions."""
    if not submissions:
        return "No submissions in this category.\n"

    # Define headers (same for both active and paid reports)
    headers = ["Contributor", "Work Title", "Value", "Wallet Address", "Reviewer", "Work Link"]
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for sub in sorted(submissions, key=lambda x: x.get('submission_date', '')): # Sort by submission date
        contributor = sub.get("contributor", "N/A")
        work_title_text = sub.get("work_title", "N/A") # Get the title text
        value = sub.get("bounty_value", "N/A")
        currency = sub.get("payment_currency", "")
        wallet = sub.get("wallet_address", "N/A")
        reviewer = sub.get("reviewer", "N/A") # Get the reviewer field
        work_link = sub.get("work_link", "#")
        # Ensure work_link is a valid link or placeholder
        work_link_md = f"[Link]({work_link})" if work_link and work_link != "#" else "N/A"
        # Get the source filename added during loading
        source_filename = sub.get("_filename", "")
        # Create the linked work title
        linked_work_title = f"[{work_title_text}](../submissions/{source_filename})" if source_filename else work_title_text


        value_str = format_value(value, currency)

        row = [
            contributor,
            linked_work_title, # Use the title linked to the source JSON
            value_str,
            # Truncate address and apply code formatting
            f"`{truncate_address(wallet)}`" if wallet != "N/A" else "N/A",
            reviewer, # Ensure reviewer is in the correct position
            work_link_md # Use the separate work link MD
        ]
        table += "| " + " | ".join(map(str, row)) + " |\n"

    return table

def write_markdown_file(output_path, title, description, grouped_submissions, status_order):
    """Writes a markdown file for the given statuses."""
    print(f"Generating Markdown for statuses: {status_order} -> {output_path}")
    markdown_content = f"# {title}\n\n"
    markdown_content += f"{description}\n\n"

    found_content = False
    for status in status_order:
        if status in grouped_submissions and grouped_submissions[status]:
            status_title = status.replace("_", " ").title()
            markdown_content += f"## {status_title}\n\n"
            markdown_content += generate_markdown_table(grouped_submissions[status])
            markdown_content += "\n"
            found_content = True

    if not found_content:
        markdown_content += "No submissions found for these statuses.\n"

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the Markdown file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Successfully generated status file at {output_path}")
    except Exception as e:
        print(f"Error writing output file {output_path}: {e}")


def main():
    """Main function to generate the active and paid payment status markdown files."""
    print("Loading submissions...")
    submissions = load_submissions()
    if not submissions:
        print("No submissions found or loaded.")
        # Create empty files or files with a message
        for file_path, title, desc in [
            (ACTIVE_STATUS_FILE, "Bounty Payment Status", "This page summarizes the status of active bounty submissions."),
            (PAID_STATUS_FILE, "Paid Bounties", "This page lists completed and paid bounty submissions.")
        ]:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{desc}\n\nNo submission data found.\n")
            print(f"Generated empty status file at {file_path}")
        return

    print(f"Loaded {len(submissions)} submissions.")
    grouped_submissions = group_by_status(submissions)
    print(f"Grouped submissions by status: {list(grouped_submissions.keys())}")

    # --- Generate Active Status Report ---
    active_statuses_present = [s for s in ACTIVE_STATUS_ORDER if s in grouped_submissions]
    # Add any other non-paid statuses found that weren't explicitly ordered (handles unexpected statuses)
    other_active_statuses = [s for s in grouped_submissions if s != PAID_STATUS and s not in active_statuses_present]
    final_active_order = active_statuses_present + sorted(other_active_statuses)

    write_markdown_file(
        ACTIVE_STATUS_FILE,
        "Bounty Payment Status",
        "This page summarizes the status of active bounty submissions (In Progress, Awaiting Review, Reviewed).",
        grouped_submissions,
        final_active_order
    )

    # --- Generate Paid Status Report ---
    write_markdown_file(
        PAID_STATUS_FILE,
        "Paid Bounties",
        "This page lists completed and paid bounty submissions.",
        grouped_submissions,
        [PAID_STATUS] # Only include the paid status
    )

if __name__ == "__main__":
    main()
