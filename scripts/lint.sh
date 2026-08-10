#!/usr/bin/env bash
set -uo pipefail

# Checks only — nothing here rewrites source. Fixing is scripts/fix.sh.
#
# Every check runs even when an earlier one fails, so one pass shows all
# the work. The script still exits non-zero if any of them failed.
#
# Unlike test.sh there is no teardown: linting needs no database, so a
# run must not disturb a stack you already have up.

status=0

docker compose run --rm --no-deps --build lint sh -c '
    rc=0
    echo "--- ruff format --check ---"
    ruff format --check . || rc=1
    echo "--- ruff check ---"
    ruff check . || rc=1
    echo "--- mypy ---"
    mypy taigun || rc=1
    exit $rc
' || status=1

exit "$status"
