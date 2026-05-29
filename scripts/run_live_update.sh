#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

"$PYTHON_BIN" -m src.bounty_finder
"$PYTHON_BIN" -m src.tests.run_bounty_check
"$PYTHON_BIN" -m src.generators.payment_status_generator
