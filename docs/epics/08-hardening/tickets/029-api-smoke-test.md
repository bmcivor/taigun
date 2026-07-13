---
type: story
project: taigun
assignee: bmcivor
---

## 29. CI smoke test against a running Taiga API server

> **Postponed 2026-07-13.** Spinning up a `taiga-back` container per CI run is
> too much infra for the observed bug rate (two NULL-field serializer crashes
> in the whole v1.0 cycle, both caught by eyeballing the lab). Coverage moved
> into 025 as an "API-render check per pushed item" step. Revisit if the class
> of bug starts appearing between dog-food passes rather than being caught by
> them.


**As a** taigun developer
**I want** CI to push tickets to a running Taiga back container and hit the Taiga API
**So that** the class of NULL-field bugs we hit twice during v1.0 dog-fooding gets caught in CI instead of by the human who notices a broken UI

**Priority:** Medium (prevents an entire class of bug that we know recurs)

### Context

The current test harness (E7) runs against `test-db` only — a Postgres container with
Taiga's schema migrations applied, but no Taiga API server. That catches:

- Writer SQL errors (`NotNullViolation`, undefined columns, etc.)
- Resolver logic against a real schema

But misses:

- API serializer crashes when a NOT-NULL-by-convention but nullable-by-schema column
  is left NULL (`tags_colors`, `tags`, `default_points_id`, ...). The Taiga back
  serializer does `dict(obj.tags_colors)` without a None-check. Our integration
  tests can't catch this because the back isn't running.

We hit two of these in this v1.0 cycle — `projects.tags_colors` and
`projects.default_points_id`. Both required manual SQL repair on the lab. Adding a
back container to the test stack lets CI catch them.

### Acceptance criteria

- New compose service in `docker-compose.yaml` running `taigaio/taiga-back:6.9.0` as
  a full API server (not just `manage.py migrate` like `test-db-init`) — listens on
  port 8000, healthcheck on `/api/v1/`
- New test stage in CI that:
  - Brings up `test-db` + `test-db-init` + `taiga-back` (the new service) +
    `test` (the existing pytest container)
  - Inside the test stage: `taigun projects create`, `taigun push` a sample of each
    ticket type, then hits the Taiga API (e.g. `GET /api/v1/projects/<id>`, `GET
    /api/v1/userstories?project=<id>`, etc.) and asserts the responses are 200 OK
    (i.e. no serializer crash)
- Failures in this stage fail the build
- A first run is green against the current writer code (catches the regression
  baseline — if any new NULL-field bug exists today that we haven't found, this
  test surfaces it)
- The stage is gated/optional if running locally without the resources for the
  full stack (decide and document — `scripts/test.sh` could take a flag like
  `--with-api` or run it conditionally on `CI=true`)

### Dependencies

- v1.0 released
