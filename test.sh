#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

"$PYTHON_BIN" -m compileall -q src scripts run.py
"$PYTHON_BIN" -m json.tool .github/submission.schema.json >/dev/null
"$PYTHON_BIN" -m json.tool src/config/constants.json >/dev/null
"$PYTHON_BIN" -m json.tool src/config/tracked_repos.json >/dev/null
"$PYTHON_BIN" -m json.tool src/config/tracked_orgs.json >/dev/null
"$PYTHON_BIN" -m json.tool src/config/extra_bounties.json >/dev/null

for file in submissions/*.json; do
  "$PYTHON_BIN" -m json.tool "$file" >/dev/null
done

ruby -e 'require "yaml"; Dir[".github/workflows/*.yml"].each { |f| YAML.load_file(f) }'
"$PYTHON_BIN" -m src.tests.run_bounty_check >/dev/null
"$PYTHON_BIN" -m pytest -q src/tests
git diff --check
