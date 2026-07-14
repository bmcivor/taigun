# Planning status

Last updated: 2026-07-13

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
- 021 complete: docker test harness — `test-db` + `test-db-init` (Taiga migrations
  + initial templates + admin user) services in `docker-compose.yaml`; `scripts/test.sh`
  orchestrates suite-level setup and teardown
- 022 complete: test suite refactored to real DB — `real_conn` fixture rolls back per
  test; `tests/factories.py` for test data setup via app code; CLI tests moved to
  `tests/cli/`; no raw SQL in test logic
- 023 complete: writer SQL bugs fixed — missing NOT NULL columns (`is_blocked`,
  `blocked_note`, `is_closed`, `client_requirement`, `team_requirement`,
  `due_date_reason`, `is_iocaine`) added to story/task/issue/epic INSERTs; bogus
  `priority_id` removed from story writer; `epics_relateduserstory.order` added;
  `cli_conn` fixture in `tests/conftest.py` routes CLI's psycopg2.connect to the test's
  open connection via SAVEPOINT so CLI tests share state with the test transaction; all
  xfails removed; 180 tests passing
- 024 complete: Jenkinsfile runs `./scripts/test.sh` (same invocation as local); test
  service's volume mount dropped so the test image is self-contained in CI; Dockerfile
  `test` stage restructured to install deps before copying code (cached layer); compose
  plugin installation added to Jenkins image in vertex-studio (separate change)
- E7 complete
- v1.0 released
- 027 complete: `Dockerfile` test stage no longer copies `docs/` (dev CLI use is native
  via `uv run`, not docker); `README.md` and `docs/ticket-format.md` corrected to reflect
  priority being issue-only; `~/.claude/skills/taigun-tickets/SKILL.md` rewritten around
  the native workflow. Original scope (separate compose service for CLI) was based on a
  wrong premise and reduced to a doc + Dockerfile cleanup
- 030 complete: dog-food audit — pushed synthetic story to `test-db`, compared against
  source, produced `docs/dog-food-audit.md` with three bugs identified: (a) As a/I want/
  So that block dropped from description, (b) blank lines between heading and content
  stripped, (c) priority silently dropped on non-issue types
- 031 complete: `BodyParser` rewritten to preserve everything between `## Title` and the
  first `### ` heading, plus blank lines within sections; `FileParser` raises `ParseError`
  if `priority:` frontmatter or `### Priority` section appears on story/task/epic (Taiga
  schema has no priority column for those types); all 35 taigun ticket files rewritten
  to move Priority inline as `**Priority:** X`; 186 tests passing (added 6 parser tests)
- 032 complete: ADR-004 written covering identification (sidecar `.taigun/state.yaml`),
  mutability (all fields mutable except identity), removal semantics (error if omitted),
  conflict semantics (detect via modified_date, prompt), missing-ticket semantics (prompt,
  default re-insert), idempotency (content hash + verbose no-op output), and audit trail
  (acting_user)
- 028 complete: `MilestoneWriter` added — milestones are created via `type: milestone`
  markdown files (frontmatter + `## Title` only; extra body content raises `ParseError`).
  FrontmatterParser accepts `estimated_start`, `estimated_finish`, `closed`. `taigun push`
  routes milestone type to the writer; output is `✓ milestone: "Sprint 3"` (no ref, since
  milestones have no ref column). `tests/factories.py::make_milestone` rewritten to use
  `MilestoneWriter` — raw-SQL exception removed
- 033 complete: sidecar state file — `taigun/state.py` implements `StateFile`
  (load/find/record/save), `locate_sidecar` (walks up from source file's directory
  looking for `.taigun/state.yaml`), and `hash_file` (sha256 of raw bytes). YAML
  format, entries stored relative to the repo root for portability. Load errors loudly
  on malformed YAML, duplicate `file_path`, or missing required fields. `taigun push`
  now loads the sidecar, refuses to re-push a source file that already has an entry
  (surfaces "already pushed as #<ref> in <project>" — actual update handling is 034's
  job), and records + saves after each successful insert
- 034 complete: update / upsert for story, task, issue, epic. New writer `update()`
  method per type. `taigun push` reads the sidecar and dispatches insert-vs-update per
  file — unchanged content is a no-op with `(unchanged) #<ref>`, an update prints
  `↺ #<ref>`, a missing-in-Taiga entry prompts to re-insert (default yes), a Taiga
  modified_date newer than last_pushed_at prompts to overwrite (default no), and
  identity changes (project or type) error loudly. `--force` skips prompts.
  Field-removal semantics per ADR-004: dropping a previously-set frontmatter field
  raises `FieldClearedError` — clear requires an explicit `field: null`. Milestone
  update is deferred to 035 with a clear error message when re-pushed
- 035 complete: milestone update via `push` (`MilestoneWriter.update()` following the
  034 pattern; no field-cleared check since milestone owner defaults to acting_user);
  `taigun projects update <slug> [--name] [--description]` — flag-driven, no source
  file, no sidecar. Entity-scoped exceptions added (`MilestoneMissingError`,
  `MilestoneConflictError`, `ProjectMissingError`). `check_taiga_conflict` /
  `check_field_cleared` helpers gained an exception-class parameter so each entity
  raises its own type. E9 complete
- 026 complete: `ConnectionManager.__init__` gained a keyword-only `_connection_factory`
  seam (defaults to `psycopg2.connect`, production behaviour unchanged); `cli_conn`
  fixture rewritten to patch `taigun.cli.ConnectionManager` with a subclass that
  injects a savepoint-scoped factory, matching the `ConfigManager` patching pattern;
  `tests/db/test_connection.py` rewritten to pass `_connection_factory=` directly
  instead of `patch("...psycopg2.connect", ...)`. No `psycopg2.connect` monkeypatching
  anywhere in the test suite
- New epic E10 opened for bugs surfaced by the 025 dog-food pass; each bug lives as
  its own ticket with a reproducer and proposed fix
- 036 complete (first E10 ticket): `locate_sidecar` now walks up twice — for an
  existing `.taigun/state.yaml` first, then for `.git/` as the repo-root marker.
  If neither is found it raises `StateError` instead of silently anchoring the
  sidecar under the first source file's directory. Three new regression tests in
  `tests/test_state.py::TestLocateSidecar`; `tests/cli/test_push.py::make_config`
  now creates `.git/` under `tmp_path` so push tests still work
- 025 dog-food re-run: fresh Taigun project on the lab, all 51 epic + story tickets
  pushed cleanly after 036 landed; every ticket carries `assignee: bmcivor`
  (mechanical mass-edit, not a taigun feature change); 037 filed for the
  `resolve_status` hard-fail surfaced by the first attempt
- 037 filed (E10): `resolve_status` fails hard on unknown status name while
  `resolve_priority` warns and falls back — proposed fix is to make status
  symmetric with priority
- New epic E11 opened for moving taigun-managed tickets out of product source
  repos into a per-user central `~/Tickets/` directory
- 038 complete (first E11 ticket): ADR-005 written and marked Accepted; covers
  layout, frontmatter contract, migration approach, and out-of-scope items
  (path is user-chosen, vertex-* migrations owned by their own repos, no
  taigun code change, no update to ADR-004)
- 037 complete: `resolve_status` now takes `Optional[str]`, falls back to the
  project default when the name is unknown or None, and logs a warning only
  when a name was given but not found — mirroring `resolve_priority` /
  `resolve_issue_type` / `resolve_severity`. `BaseWriter._resolve_status`
  simplified to a thin delegate now that the resolver handles both cases.
  Three regression tests in `TestResolveStatus` (falls back on unknown,
  warns on fallback, None returns default silently); old raise-on-unknown
  test removed
- 039 complete: taigun's own `docs/epics/` tree copied to `~/Tickets/taigun/docs/epics/`;
  sidecar copied to `~/Tickets/.taigun/state.yaml` with `file_path` values
  rewritten from `docs/epics/…` to `taigun/docs/epics/…`. Verification push
  from `~/Tickets/` reported 48 `(unchanged)` + 3 legitimate updates (for
  037/038/039 which had genuinely changed since the last mass-edit push).
  Source-repo commit removed all 51 ticket files under `docs/epics/` and
  the untracked `.taigun/`. `~/Tickets/` was `git init`'d for a future
  local-only history option; no remote configured
- 040 complete (E11 closed): README gained a "Where to put your tickets"
  section explaining the central `~/Tickets/` layout, the anti-pattern of
  committing tickets into product repos, and the sidecar seeding step for a
  fresh directory. Pushing-tickets section updated with the full output
  vocabulary (`(unchanged)`, `↺ updated`, `↷ skipped`, `~ dry-run`) and the
  update / `--force` semantics. `docs/ticket-format.md` gained a one-line
  pointer back to the README. `taigun-tickets` skill moved into the repo at
  `.claude/skills/taigun-tickets/SKILL.md` and rewritten for the central-dir
  workflow; the user-scoped copy at `~/.claude/skills/…` is kept in sync as
  a byte-identical mirror. E11 done

## What's next

- Cross-repo migration campaign (per [docs/migration-plan.md](migration-plan.md),
  local working notes): vertex-play mass-edit + migration, vertex-block
  conversion + migration

## Postponed

- 029 (CI smoke test against a running Taiga API server): spinning up a
  `taiga-back` container per CI run is too much infra for the observed bug
  rate (two NULL-field serializer crashes in the whole v1.0 cycle, both
  caught by eyeballing the lab). Coverage folded into 025. Revisit if this
  class of bug starts appearing between dog-food passes

## Key decisions

- Direct DB writes over API wrapper — see ADR-001
- Markdown + YAML frontmatter ticket format derived from vertex-play convention — see ADR-002
- Postgres exposed on Tailscale interface only, hostname resolved dynamically in Ansible — see ADR-003
- Update workflow uses a sidecar file (`.taigun/state.yaml`) for source-to-ref mapping — see ADR-004
- Taiga images pinned to `6.9.0` via `docker-compose.override.yml` deployed by the taiga role
- `tailscale_hostname` added as a shared variable in vertex-studio `vars.yaml`; `jenkins_url`
  refactored to use it
- Build backend: `setuptools` (chosen for ubiquity over hatchling/flit-core)
- Version management: `python-semantic-release` (parses conventional commits to determine
  bump level; runs in a Docker container via `scripts/release.sh`)
