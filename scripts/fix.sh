#!/usr/bin/env bash
set -uo pipefail

# The write counterpart to lint.sh — everything here modifies source.
# Runs against the `lint` service so writes reach the host through the
# bind mount. --user "$(id -u):$(id -g)" prevents root-owned files
# appearing on your filesystem.
#
# Every step runs even when an earlier one fails, and the script exits
# non-zero if any of them did.
#
# No teardown, for the same reason as lint.sh: a run must not disturb
# a stack you already have up.

status=0

docker compose run --rm --no-deps --build --user "$(id -u):$(id -g)" lint sh -c '
    rc=0
    echo "--- ruff format ---"
    uv run ruff format . || rc=1
    echo "--- ruff check --fix ---"
    uv run ruff check --fix . || rc=1
    exit $rc
' || status=1

exit "$status"
