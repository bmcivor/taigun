## 22. Refactor tests to real DB with fixture utilities

**Epic:** E7 — Integration testing & correctness

**As a** developer
**I want** every DB-related test to run against `test-db` using real connections and
composable fixtures, with no mocks anywhere
**So that** a green test suite means the SQL actually works against a real Taiga schema

### Acceptance criteria

- Set of fixture utilities in `tests/db/factories.py` (or similar): functions like
  `make_project`, `make_user`, `make_milestone`, `make_epic`, `make_status`, etc., each
  taking a connection and emitting real INSERTs, returning the inserted IDs
- Pytest fixtures wrap these so tests can request what they need (e.g.
  `def test_x(real_conn, project, user): ...`)
- New `real_conn` fixture in `tests/db/conftest.py` yields a psycopg2 connection to
  `test-db` from `TEST_DB_URL`
- Each test wrapped in a SAVEPOINT that rolls back on teardown — writes don't leak
  between tests, baseline init data persists
- Every existing mock removed:
  - `mock_conn` / `mock_cursor` in `tests/db/conftest.py` deleted
  - Writer test assertions change from "SQL string ==" to "perform write, then SELECT
    and assert column values"
  - Resolver tests do real lookups against fixture-created data
  - CLI tests stop mocking `_WRITERS`, `Lister`, and `ConnectionManager` — they hit
    `test-db` end-to-end
- Parser, model, and config tests stay as-is (no DB involvement)

### Dependencies

- 021

### Blocks

- 023

### Priority

- High
