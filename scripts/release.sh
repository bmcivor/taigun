#!/usr/bin/env bash
set -euo pipefail

docker compose run --rm --build \
    --user "$(id -u):$(id -g)" \
    -e GIT_AUTHOR_NAME="$(git config user.name)" \
    -e GIT_AUTHOR_EMAIL="$(git config user.email)" \
    -e GIT_COMMITTER_NAME="$(git config user.name)" \
    -e GIT_COMMITTER_EMAIL="$(git config user.email)" \
    release semantic-release "$@"
