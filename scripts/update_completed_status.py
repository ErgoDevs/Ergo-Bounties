import json
from pathlib import Path

SUBMISSIONS_DIR = Path("submissions")
IGNORE_FILES = {"example-user-ergoscript-fsmtest.json"}
OLD_STATUS = "completed"
NEW_STATUS = "awaiting-review"

def update_status_in_file(filepath):
    """Reads a JSON file and updates the status if it matches OLD_STATUS."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        current_status = data.get("status", "").lower()

        if current_status == OLD_STATUS:
            print(f"Updating status in {filepath.name} from '{OLD_STATUS}' to '{NEW_STATUS}'...")
            data["status"] = NEW_STATUS
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write('\n') # Add trailing newline
            return True
        else:
            # print(f"Skipping {filepath.name}: Status is '{current_status}' (not '{OLD_STATUS}').")
            return False

    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath.name}")
        return False
    except Exception as e:
        print(f"Error processing {filepath.name}: {e}")
        return False

def main():
    """Main function to iterate through submissions and update status."""
    print(f"Starting status update process: '{OLD_STATUS}' -> '{NEW_STATUS}'")
    updated_count = 0
    skipped_count = 0
    error_count = 0

    if not SUBMISSIONS_DIR.is_dir():
        print(f"Error: Submissions directory not found at {SUBMISSIONS_DIR}")
        return

    for filepath in SUBMISSIONS_DIR.glob("*.json"):
        if filepath.name in IGNORE_FILES:
            # print(f"Ignoring file: {filepath.name}")
            continue

        try:
            updated = update_status_in_file(filepath)
            if updated:
                updated_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"Critical error processing {filepath.name}: {e}")
            error_count += 1

    print("\n--- Status Update Summary ---")
    print(f"Files updated: {updated_count}")
    print(f"Files skipped (status did not match '{OLD_STATUS}'): {skipped_count}")
    print(f"Files with processing errors: {error_count}")
    print("-----------------------------")

if __name__ == "__main__":
    main()
