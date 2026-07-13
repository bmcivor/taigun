---
type: story
project: taigun
assignee: bmcivor
status: Done
---

## 27. Separate compose service for taigun CLI invocations

**As a** taigun developer
**I want** a dedicated docker-compose service for running the taigun CLI against the lab Taiga
**So that** the `test` image stays focused on running tests, and ad-hoc CLI use doesn't require bind-mounting or baking docs into the test image

**Priority:** Medium

### Context

Right now, running taigun against the lab Taiga (or `test-db` for dry-runs) reuses the
`test` compose service and either:

- Bakes `docs/` into the test image via a `COPY docs/ ./docs/` in the Dockerfile (the
  current state — done as the agreed temporary fix), OR
- Adds a one-off volume mount and reverts it after

Both are hacks. The clean shape is a separate `taigun` (or `cli`) compose service
that:

- Uses the existing `release` build stage from the Dockerfile (or a thin variant)
- Mounts a config directory so the taigun config file persists between runs
- Mounts whatever ticket directories are needed (`./docs/`, vertex-play repo, etc.)
  via compose-relative paths
- Is invoked via a `scripts/cli.sh` (or similar) wrapper

### Acceptance criteria

- New `taigun` (or `cli`) service defined in `docker-compose.yaml` using an
  appropriate build target
- Service has a sensible default command (e.g. `taigun --help`) but accepts
  arbitrary CLI args via `docker compose run --rm cli <args>`
- Config persistence via volume mount — running `taigun configure` once and a
  subsequent `taigun push` should work without re-seeding the config
- `COPY docs/ ./docs/` removed from the test stage in `Dockerfile`
- A short usage doc (`docs/cli-usage.md` or a section in README) shows how to invoke
  the new service for the common flows: configure, projects list, push
- All 180 existing tests still pass (the test stage and CI path are unchanged)

### Dependencies

- v1.0 released
