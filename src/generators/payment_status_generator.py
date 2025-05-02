import os
import json
from collections import defaultdict
from pathlib import Path

SUBMISSIONS_DIR = Path("submissions")
OUTPUT_FILE = Path("data/payment_status.md")
STATUS_ORDER = ["ready_for_payment", "in-progress", "completed", "paid", "cancelled"] # Prioritize ready_for_payment
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

    # Ensure correct headers including Reviewer
    headers = ["Contributor", "Work Title", "Value", "Wallet Address", "Reviewer", "Work Link", "Source File"]
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for sub in sorted(submissions, key=lambda x: x.get('submission_date', '')): # Sort by submission date
        contributor = sub.get("contributor", "N/A")
        work_title = sub.get("work_title", "N/A")
        value = sub.get("bounty_value", "N/A")
        currency = sub.get("payment_currency", "")
        wallet = sub.get("wallet_address", "N/A")
        reviewer = sub.get("reviewer", "N/A") # Get the reviewer field
        work_link = sub.get("work_link", "#")
        # Ensure work_link is a valid link or placeholder
        link_text = f"[Link]({work_link})" if work_link and work_link != "#" else "N/A"
        # Get the source filename added during loading
        source_filename = sub.get("_filename", "")
        # Create a relative link with simplified text
        source_link = f"[submission](../submissions/{source_filename})" if source_filename else "N/A"


        value_str = format_value(value, currency)

        row = [
            contributor,
            work_title,
            value_str,
            # Truncate address and apply code formatting
            f"`{truncate_address(wallet)}`" if wallet != "N/A" else "N/A",
            reviewer, # Ensure reviewer is in the correct position
            link_text,
            source_link # Ensure source link is in the correct position
        ]
        table += "| " + " | ".join(map(str, row)) + " |\n"

    return table

def main():
    """Main function to generate the payment status markdown file."""
    print("Loading submissions...")
    submissions = load_submissions()
    if not submissions:
        print("No submissions found or loaded.")
        # Create an empty file or a file with a message
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("# Bounty Payment Status\n\n")
            f.write("No submission data found.\n")
        print(f"Generated empty status file at {OUTPUT_FILE}")
        return

    print(f"Loaded {len(submissions)} submissions.")
    grouped_submissions = group_by_status(submissions)
    print(f"Grouped submissions by status: {list(grouped_submissions.keys())}")

    # Determine the order of statuses in the output file
    present_statuses = sorted(grouped_submissions.keys())
    ordered_statuses = [s for s in STATUS_ORDER if s in present_statuses]
    ordered_statuses += [s for s in present_statuses if s not in STATUS_ORDER] # Add any other statuses found

    print(f"Generating Markdown for statuses: {ordered_statuses}")
    markdown_content = "# Bounty Payment Status\n\n"
    markdown_content += "This page summarizes the status of bounty submissions.\n\n"

    for status in ordered_statuses:
        status_title = status.replace("_", " ").title()
        markdown_content += f"## {status_title}\n\n"
        markdown_content += generate_markdown_table(grouped_submissions[status])
        markdown_content += "\n"

    # Ensure the output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write the Markdown file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Successfully generated payment status file at {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing output file {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    main()
