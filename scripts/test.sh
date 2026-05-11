#!/usr/bin/env bash
set -euo pipefail

cleanup() {
    docker compose down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

cleanup
docker compose run --rm test "$@"
