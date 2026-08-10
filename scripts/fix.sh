#!/usr/bin/env bash
set -uo pipefail

# The write counterpart to lint.sh — everything here modifies source.
#
# The source mount is passed inline rather than declared on the `lint`
# service: Jenkins runs lint.sh against the same service under
# docker-in-docker, where a bind mount resolves against the host daemon
# and lands an empty /app in the container. fix.sh is developer-local
# only, so the mount is safe here.
#
# --user "$(id -u):$(id -g)" keeps the rewritten files owned by you
# rather than root.
#
# Every step runs even when an earlier one fails, and the script exits
# non-zero if any of them did.
#
# No teardown, for the same reason as lint.sh: a run must not disturb
# a stack you already have up.

status=0

docker compose run --rm --no-deps --build \
    --user "$(id -u):$(id -g)" \
    --volume "$PWD:/app" \
    lint sh -c '
    rc=0
    echo "--- ruff check --fix ---"
    ruff check --fix . || rc=1
    echo "--- ruff format ---"
    ruff format . || rc=1
    exit $rc
' || status=1

exit "$status"
