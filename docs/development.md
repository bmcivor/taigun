# Development

## Environment

The project is a `uv`-managed Python package (3.11+). Dependencies are pinned
exactly in `pyproject.toml`; `uv run taigun ...` runs the CLI from source.

```
uv sync --group dev
```

Creates `.venv/` in the repo root with the runtime and development
dependencies — pytest, ruff, mypy — installed.

## Adding a dependency

```
uv add <package>                # runtime
uv add --group dev <package>    # development only
```

Both rewrite `pyproject.toml` and `uv.lock`. Commit the two together: the
release process regenerates the lockfile and will fail if it has drifted from
the manifest.

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

## Quality checks

```
./scripts/lint.sh
```

Runs `ruff format --check`, `ruff check`, and `mypy` in that order. Nothing is
rewritten — every check runs even when an earlier one fails, so a single pass
shows all the work, and the script exits non-zero if any of them did. No
database is needed, and there is no teardown, so a run will not disturb a
stack you already have up.

```
./scripts/fix.sh
```

The write counterpart: `ruff check --fix` then `ruff format`, applied to your
working tree. Mounts the source into the container and runs as your own user,
so the rewritten files are not left root-owned. Anything ruff cannot fix
automatically is left for you — re-run `./scripts/lint.sh` to see what remains.

## What CI runs

Jenkins runs three stages, defined in the `Jenkinsfile`:

- **Docs** — builds this site with `--strict`, so a broken link or a page
  missing from the nav fails the build
- **Test** — `./scripts/test.sh`
- **Lint** — `./scripts/lint.sh`

All three are the same commands you run locally, so a green local run is
representative.

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
