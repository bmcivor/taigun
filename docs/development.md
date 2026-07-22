# Development

## Environment

The project is a `uv`-managed Python package (3.11+). Dependencies are pinned
exactly in `pyproject.toml`; `uv run taigun ...` runs the CLI from source.

## Running the tests

```
./scripts/test.sh
```

The suite runs inside Docker against a real Taiga schema — no mocked SQL. The
compose file wires three services:

- `test-db` — PostgreSQL
- `test-db-init` — a `taiga-back` container that runs Django migrations, loads
  the initial project templates, and creates an admin user
- `test` — the pytest run, once the schema is ready

`scripts/test.sh` tears the stack down before and after, so runs are clean.
Arguments are forwarded to pytest:

```
./scripts/test.sh tests/db/test_story.py -k update
```

CI (Jenkins) runs the same script, so a green local run is representative.

## Serving the docs

```
docker compose up docs
```

Serves this site on [http://localhost:8000](http://localhost:8000) via
mkdocs-material, live-reloading on changes.

## Releasing

Releases are cut from the `tag-release` branch using
[python-semantic-release](https://python-semantic-release.readthedocs.io/),
inside a container that passes your local git identity through:

```
git checkout tag-release
./scripts/release.sh --noop version --minor   # dry run
./scripts/release.sh version --minor          # bump, commit, tag
git push origin tag-release --tags
```

The `--minor` (or `--major` / `--patch`) flag forces a bump level; drop it to let
semantic-release derive the bump from conventional commit messages since the last
tag. `--noop` is a global flag and must come before the `version` subcommand.
