## 21. Docker test harness

**Epic:** E7 — Integration testing & correctness

**As a** developer
**I want** a Docker-based test database with a real Taiga schema and baseline data
**So that** tests run against the actual Taiga DB structure rather than mocks or
hand-written fixtures

### Acceptance criteria

- New `test-db` service in `docker-compose.yaml`: pinned Postgres image matching what
  Taiga 6.9.0 expects, healthcheck that succeeds when accepting connections
- New `test-db-init` service using `taigaio/taiga-back:6.9.0` as a one-shot job:
  runs Django migrations against `test-db`, creates a baseline admin user and a
  baseline project (so signal-derived data — per-project sequence, default statuses,
  priorities, severities, issue types, content type rows — is present), then exits
- Existing `test` service depends on both: `test-db` healthy and `test-db-init` exited
  successfully
- `TEST_DB_URL` env var passed into the `test` container
- No redis, no full Taiga app running — only `test-db` is alive once init completes

### Dependencies

- None

### Blocks

- 022, 024

### Priority

- High
