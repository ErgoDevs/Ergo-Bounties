#!/usr/bin/env python3
"""Validate generated bounty output files."""

import logging
import json
import re
import sys
from pathlib import Path

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
    COLORED_OUTPUT = True
except ImportError:
    COLORED_OUTPUT = False

    class DummyStyle:
        def __getattr__(self, name):
            return ""

    Fore = DummyStyle()
    Style = DummyStyle()


SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.resolve()
BOUNTIES_DIR = PROJECT_ROOT / "data"
README_PATH = PROJECT_ROOT / "README.md"
EXTRA_BOUNTIES_PATH = PROJECT_ROOT / "src" / "config" / "extra_bounties.json"
MANUAL_BOUNTY_REQUIRED_FIELDS = {
    "owner",
    "repo",
    "title",
    "url",
    "amount",
    "currency",
    "primary_lang",
    "issue_number",
    "creator",
    "status",
}

logging.basicConfig(
    level=logging.INFO,
    format=(
        f"{Fore.CYAN}%(asctime)s{Style.RESET_ALL} - %(message)s"
        if COLORED_OUTPUT
        else "%(asctime)s - %(message)s"
    ),
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bounty_check")


def print_header(title: str) -> None:
    width = 80
    line = "=" * width
    if COLORED_OUTPUT:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{line}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{title.center(width)}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{line}{Style.RESET_ALL}\n")
    else:
        print(f"\n{line}")
        print(title.center(width))
        print(f"{line}\n")


def print_status(message: str, status: bool, details: str = "") -> None:
    status_text = "PASS" if status else "FAIL"
    if COLORED_OUTPUT:
        color = Fore.GREEN if status else Fore.RED
        status_text = f"{color}{status_text}{Style.RESET_ALL}"
        print(f"{Fore.WHITE}{message}:{' ' * max(1, 50 - len(message))}{status_text}  {details}")
    else:
        print(f"{message}:{' ' * max(1, 50 - len(message))}{status_text}  {details}")


def validate_output_files(bounties_dir: Path) -> bool:
    logger.info("Validating output files in %s...", bounties_dir)
    overall_success = True

    key_files = [
        "all.md",
        "summary.md",
        "featured_bounties.md",
        "currency_prices.md",
        "high-value-bounties.md",
        "new-bounties.md",
        "recently-active.md",
        "stale-bounties.md",
        "starter-bounties.md",
    ]

    for filename in key_files:
        file_path = bounties_dir / filename
        if file_path.exists() and file_path.stat().st_size > 0:
            print_status(f"Checking {filename}", True, "Found and not empty.")
        else:
            details = "Not found." if not file_path.exists() else "File is empty."
            print_status(f"Checking {filename}", False, details)
            overall_success = False

    for subdir_name in ["by_language", "by_currency", "by_org"]:
        subdir_path = bounties_dir / subdir_name
        if not subdir_path.is_dir():
            print_status(f"Checking {subdir_name}/ directory", False, "Directory not found.")
            overall_success = False
            continue

        md_files = list(subdir_path.glob("*.md"))
        non_empty_md_files = [path for path in md_files if path.stat().st_size > 0]
        if non_empty_md_files:
            print_status(
                f"Checking {subdir_name}/ directory",
                True,
                f"Found {len(non_empty_md_files)} non-empty file(s).",
            )
        elif md_files:
            print_status(
                f"Checking {subdir_name}/ directory",
                False,
                "Directory exists, but all .md files are empty.",
            )
            overall_success = False
        else:
            print_status(
                f"Checking {subdir_name}/ directory",
                False,
                "Directory exists, but contains no .md files.",
            )
            overall_success = False

    all_bounties = bounties_dir / "all.md"
    if all_bounties.exists():
        issue_urls = re.findall(
            r"https://github\.com/[^)\s]+/(?:issues|pull)/\d+",
            all_bounties.read_text(encoding="utf-8"),
        )
        normalized = [url.lower() for url in issue_urls if "ergodevs/ergo-bounties/new/" not in url.lower()]
        duplicates = sorted({url for url in normalized if normalized.count(url) > 1})
        if duplicates:
            print_status("Checking duplicate bounty URLs", False, f"Found {len(duplicates)} duplicate(s).")
            overall_success = False
        else:
            print_status("Checking duplicate bounty URLs", True, "No duplicates.")

    summary_file = bounties_dir / "summary.md"
    high_value_file = bounties_dir / "high-value-bounties.md"
    if summary_file.exists() and README_PATH.exists():
        summary_text = summary_file.read_text(encoding="utf-8")
        readme_text = README_PATH.read_text(encoding="utf-8")
        total_match = re.search(r"\| \*\*Total\*\* \| \*\*(\d+)\*\* \| \*\*([\d,]+\.\d{2}) ERG\*\* \|", summary_text)
        open_badge = re.search(r"Open%20Bounties-(\d+)(?:\+|%2B)?-4CAF50", readme_text)
        value_badge = re.search(r"Total%20Value-([\d,]+\.\d{2})%20ERG-2196F3", readme_text)
        if not total_match or not open_badge or not value_badge:
            print_status("Checking README summary badges", False, "Could not parse summary or README badges.")
            overall_success = False
        else:
            summary_count, summary_value = total_match.groups()
            if summary_count != open_badge.group(1) or summary_value != value_badge.group(1):
                print_status(
                    "Checking README summary badges",
                    False,
                    f"README has {open_badge.group(1)} / {value_badge.group(1)}, summary has {summary_count} / {summary_value}.",
                )
                overall_success = False
            else:
                print_status("Checking README summary badges", True, "README matches summary totals.")

    if high_value_file.exists() and README_PATH.exists():
        high_value_text = high_value_file.read_text(encoding="utf-8")
        readme_text = README_PATH.read_text(encoding="utf-8")
        high_value_count = re.search(r"Total high-value bounties: \*\*(\d+)\*\*", high_value_text)
        high_value_badge = re.search(r"High%20Value-(\d+)(?:\+|%2B)?%20Over%201000%20ERG-FFC107", readme_text)
        if not high_value_count or not high_value_badge:
            print_status("Checking README high-value badge", False, "Could not parse high-value count or README badge.")
            overall_success = False
        elif high_value_count.group(1) != high_value_badge.group(1):
            print_status(
                "Checking README high-value badge",
                False,
                f"README has {high_value_badge.group(1)}, high-value page has {high_value_count.group(1)}.",
            )
            overall_success = False
        else:
            print_status("Checking README high-value badge", True, "README matches high-value page.")

    if EXTRA_BOUNTIES_PATH.exists():
        try:
            extra_bounties = json.loads(EXTRA_BOUNTIES_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print_status("Checking manual bounty config", False, f"Invalid JSON: {exc}")
            return False

        config_ok = isinstance(extra_bounties, list)
        bad_entries = []
        if config_ok:
            for index, bounty in enumerate(extra_bounties):
                if not isinstance(bounty, dict):
                    bad_entries.append(f"entry {index} is not an object")
                    continue
                missing = sorted(field for field in MANUAL_BOUNTY_REQUIRED_FIELDS if not str(bounty.get(field, "")).strip())
                if missing:
                    bad_entries.append(f"entry {index} missing {', '.join(missing)}")
                url = str(bounty.get("url", "")).strip()
                if url and not (url.startswith("https://") or url.startswith("http://") or url.startswith("#")):
                    bad_entries.append(f"entry {index} has unsupported url {url}")
                amount = str(bounty.get("amount", "")).strip()
                if amount not in {"Ongoing", "Not specified"}:
                    try:
                        if float(amount) <= 0:
                            bad_entries.append(f"entry {index} amount must be positive")
                    except ValueError:
                        bad_entries.append(f"entry {index} amount is not numeric/Ongoing/Not specified")
        if not config_ok:
            print_status("Checking manual bounty config", False, "Expected a list.")
            overall_success = False
        elif bad_entries:
            print_status("Checking manual bounty config", False, "; ".join(bad_entries[:3]))
            overall_success = False
        else:
            print_status("Checking manual bounty config", True, "Manual bounties are structurally valid.")

    if overall_success:
        logger.info("All required output files validated successfully.")
    else:
        logger.error("Some output files/directories failed validation.")

    return overall_success


def main() -> int:
    print_header("Ergo Bounties Output Validation")
    logger.info("Validating output in directory: %s", BOUNTIES_DIR)
    return 0 if validate_output_files(BOUNTIES_DIR) else 1


if __name__ == "__main__":
    sys.exit(main())
