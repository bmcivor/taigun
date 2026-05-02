# Planning status

Last updated: 2026-05-03

## What's done

- Spec, ticket format, and ADRs (001–003) written in `docs/`
- All 6 epics outlined and ordered in `docs/epics.md`
- All 19 tickets written across E1–E6
- E1 complete: Postgres exposed over Tailscale, Taiga images pinned, Jenkins URL
  refactored to use `tailscale_hostname` variable — all merged to master in vertex-studio
- DB connectivity verified from dev machine over Tailscale (002)
- 003 complete: `pyproject.toml`, `taigun/` package structure, stub CLI, `uv.lock`
- 004 complete: config module (`load_config`, `save_config`), tests, Dockerfile, docker-compose,
  Jenkinsfile — CI running on MRs in Jenkins
- `jenkins_url` fixed to include port 8083 in vertex-studio
- 005 complete: `models.py` — Story, Issue, Task, Epic dataclasses
- 006 complete: `parsers/frontmatter.py` — FrontmatterParser; `exceptions.py` — ParseError;
  parsers refactored to class-based design under `taigun/parsers/`
- 007 complete: `parsers/body.py` — BodyParser; `parsers/file.py` — FileParser
- `config.py` refactored to ConfigManager class (injectable path)
- E3 complete
- 008 complete: `db.py` — ConnectionManager; commit/rollback context manager
- 009 complete: `resolver.py` — Resolver class; ResolveError in `exceptions.py`
- 010 complete: `db/ref.py` — `allocate_ref` for per-project ref counters
- 011 complete: `db/story.py` — `insert_story` writer; full transaction, returns ref
- 012 complete: `db/issue.py` — IssueWriter; resolver fallback for issue_type and severity
- 013 complete: `db/task.py` — TaskWriter; resolve_story added to Resolver
- 014 complete: `db/epic.py` — EpicWriter; random color generation
- BaseWriter ABC extracted to `db/base.py`; shared logic (_resolve_common, _resolve_status,
  _allocate_and_set_ref) consolidated; status tests moved to test_base.py; E4 complete
- 015 complete: `taigun configure` — interactive profile setup with connection test
- 016 complete: `taigun push` — multi-file push, dry-run, per-file failure handling,
  exit codes; `ConnectionManager.connect(dry_run=)` added
- Test suite refactored: `tests/db/conftest.py` with shared fixtures; class-level fixtures
  throughout; real ConfigManager and FileParser used in CLI tests
- 017 complete: `taigun projects list`, `taigun epics list`, `taigun statuses list`;
  `db/lister.py` — Lister class; E5 complete
- 018 complete: PyPI-ready `pyproject.toml` (PEP 639 license, classifiers, urls, authors);
  MIT LICENSE file; expanded README; `uv build` produces clean wheel + sdist
- Build backend swapped from hatchling to `setuptools==82.0.1`
- All runtime and dev dependencies pinned exactly with `==` in `pyproject.toml`
- `python-semantic-release==9.21.1` wired up for version bumping (dev dep + `[tool.semantic_release]` config); release branch configured as `tag-release`
- Release container scaffolding: `release` Dockerfile stage with git, `release` service in
  docker-compose, `scripts/release.sh` wrapper that passes host git identity into the container
- `UV_PROJECT_ENVIRONMENT=/opt/venv` in Dockerfile base stage so the image's venv lives
  outside the volume mount (fixes root-owned `.venv` on host after docker runs)

## What's next

- Use it in anger: populate vertex-play tickets to the lab Taiga instance (covers 019)
- 0.1.0 cut once the run-through is clean
- 1.0.0 once it's been demonstrably stable

## Key decisions

- Direct DB writes over API wrapper — see ADR-001
- Markdown + YAML frontmatter ticket format derived from vertex-play convention — see ADR-002
- Postgres exposed on Tailscale interface only, hostname resolved dynamically in Ansible — see ADR-003
- Taiga images pinned to `6.9.0` via `docker-compose.override.yml` deployed by the taiga role
- `tailscale_hostname` added as a shared variable in vertex-studio `vars.yaml`; `jenkins_url`
  refactored to use it
- Build backend: `setuptools` (chosen for ubiquity over hatchling/flit-core)
- Version management: `python-semantic-release` (parses conventional commits to determine
  bump level; runs in a Docker container via `scripts/release.sh`)
