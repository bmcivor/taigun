# Planning status

Last updated: 2026-04-30

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

## What's next

- 010: ref allocation

## Key decisions

- Direct DB writes over API wrapper — see ADR-001
- Markdown + YAML frontmatter ticket format derived from vertex-play convention — see ADR-002
- Postgres exposed on Tailscale interface only, hostname resolved dynamically in Ansible — see ADR-003
- Taiga images pinned to `6.9.0` via `docker-compose.override.yml` deployed by the taiga role
- `tailscale_hostname` added as a shared variable in vertex-studio `vars.yaml`; `jenkins_url`
  refactored to use it
