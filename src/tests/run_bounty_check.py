#!/usr/bin/env python3
"""Validate generated bounty output files."""

import logging
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
