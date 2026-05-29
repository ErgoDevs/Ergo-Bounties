#!/usr/bin/env python3
"""Lightweight workflow sanity checks without network access."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def test_required_workflows_exist() -> bool:
    required = {
        "update-bounties.yml",
        "update-on-merge.yml",
        "update-payment-status.yml",
        "triage-submission-prs.yml",
        "ops-status.yml",
    }
    existing = {path.name for path in WORKFLOWS.glob("*.yml")}
    missing = sorted(required - existing)
    if missing:
        print(f"Missing workflows: {', '.join(missing)}")
        return False
    return True


def test_removed_workflows_stay_removed() -> bool:
    removed = {"tag-author.yml", "validate-submission-status.yml"}
    existing = {path.name for path in WORKFLOWS.glob("*.yml")}
    unexpected = sorted(removed & existing)
    if unexpected:
        print(f"Removed workflows still present: {', '.join(unexpected)}")
        return False
    return True


def test_no_known_bad_workflow_refs() -> bool:
    text = "\n".join(path.read_text(encoding="utf-8") for path in WORKFLOWS.glob("*.yml"))
    bad = ["tj-actions/changed-files", "PAT_TOKEN", "continue-on-error: true"]
    found = [item for item in bad if item in text]
    if found:
        print(f"Unsafe workflow references found: {', '.join(found)}")
        return False
    return True


def test_workflow_script_paths_exist() -> bool:
    paths = [
        ROOT / "src" / "bounty_finder.py",
        ROOT / "src" / "tests" / "run_bounty_check.py",
        ROOT / "src" / "generators" / "payment_status_generator.py",
        ROOT / "scripts" / "triage_submission_prs.py",
        ROOT / "scripts" / "update_ops_issue.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.exists()]
    if missing:
        print(f"Workflow script paths missing: {', '.join(missing)}")
        return False
    return True


def main() -> int:
    checks = [
        test_required_workflows_exist,
        test_removed_workflows_stay_removed,
        test_no_known_bad_workflow_refs,
        test_workflow_script_paths_exist,
    ]
    return 0 if all(check() for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
