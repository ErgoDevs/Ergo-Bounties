import os # Import os for path.getmtime
import json
import datetime # Import datetime
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.common import escape_markdown_cell, escape_markdown_link_text

SUBMISSIONS_DIR = Path("submissions")
# Update output paths to be inside the submissions directory
ACTIVE_STATUS_FILE = SUBMISSIONS_DIR / "payment_status.md"
PAID_STATUS_FILE = SUBMISSIONS_DIR / "paid.md"
PAYMENT_QUEUE_FILE = SUBMISSIONS_DIR / "payment_queue.md"
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
            # Get last modified time before opening
            last_modified_timestamp = os.path.getmtime(filename)
            last_modified_date = datetime.datetime.fromtimestamp(last_modified_timestamp).strftime('%Y-%m-%d')

            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Add filename and last modified date for reference
                data['_filename'] = filename.name
                data['_last_modified_date'] = last_modified_date
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

    # Add "Last Updated" header
    headers = ["Contributor", "Work Title", "Value", "Wallet Address", "Reviewer", "Work Link", "Last Updated"]
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    # Sort by last modified date descending (most recent first)
    for sub in sorted(submissions, key=lambda x: x.get('_last_modified_date', '0000-00-00'), reverse=True):
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
        # Adjust link: MD file is now in the same dir as JSON file
        linked_work_title = (
            f"[{escape_markdown_link_text(work_title_text)}]({source_filename})"
            if source_filename
            else escape_markdown_cell(work_title_text)
        )
        # Get the last modified date
        last_modified_date = sub.get("_last_modified_date", "N/A")


        value_str = format_value(value, currency)

        row = [
            escape_markdown_cell(contributor),
            linked_work_title, # Use the title linked to the source JSON
            escape_markdown_cell(value_str),
            # Truncate address and apply code formatting
            f"`{escape_markdown_cell(truncate_address(wallet))}`" if wallet != "N/A" else "N/A",
            escape_markdown_cell(reviewer), # Ensure reviewer is in the correct position
            work_link_md, # Use the separate work link MD
            escape_markdown_cell(last_modified_date) # Add last updated date
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


def generate_payment_queue(reviewed_submissions):
    """Writes a focused payment queue for reviewed, unpaid submissions."""
    markdown_content = "# Payment Queue\n\n"
    markdown_content += "Reviewed submissions waiting for payment.\n\n"

    if not reviewed_submissions:
        markdown_content += "No submissions waiting for payment.\n"
    else:
        headers = ["Contributor", "Work Title", "Value", "Wallet Address", "Reviewer", "Work Link", "Submitted"]
        markdown_content += "| " + " | ".join(headers) + " |\n"
        markdown_content += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for sub in sorted(reviewed_submissions, key=lambda x: x.get("submission_date", "0000-00-00")):
            work_link = sub.get("work_link", "")
            work_link_md = f"[Link]({work_link})" if work_link else "N/A"
            filename = sub.get("_filename", "")
            title = sub.get("work_title", "N/A")
            title_md = (
                f"[{escape_markdown_link_text(title)}]({filename})"
                if filename
                else escape_markdown_cell(title)
            )
            row = [
                escape_markdown_cell(sub.get("contributor", "N/A")),
                title_md,
                escape_markdown_cell(format_value(sub.get("bounty_value", "N/A"), sub.get("payment_currency", ""))),
                f"`{escape_markdown_cell(sub.get('wallet_address', 'N/A'))}`",
                escape_markdown_cell(sub.get("reviewer", "N/A")),
                work_link_md,
                escape_markdown_cell(sub.get("submission_date", "N/A")),
            ]
            markdown_content += "| " + " | ".join(map(str, row)) + " |\n"

    PAYMENT_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PAYMENT_QUEUE_FILE, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"Successfully generated payment queue at {PAYMENT_QUEUE_FILE}")


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

    generate_payment_queue(grouped_submissions.get("reviewed", []))

if __name__ == "__main__":
    main()
