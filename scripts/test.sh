#!/usr/bin/env bash
set -euo pipefail

cleanup() {
    docker compose down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

cleanup

if [[ $# -gt 0 ]]; then
    docker compose run --rm --build --user "$(id -u):$(id -g)" test pytest "$@"
else
    docker compose run --rm --build --user "$(id -u):$(id -g)" test pytest tests/ -v --cov-fail-under=90
fi
