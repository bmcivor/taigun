## ~~8. DB connection management~~ (Done)

**Epic:** E4 — DB layer

**As a** developer
**I want** a db.py module that opens and manages a Postgres connection from config
**So that** all DB operations share a single connection layer with consistent error handling

### Acceptance criteria

- `db.py` exposes a context manager `get_connection(config)` using `psycopg2`
- Connection errors (wrong host, bad credentials, unreachable) surface with a clear
  message — no raw psycopg2 tracebacks shown to the user
- Context manager commits on clean exit, rolls back on exception
- No connection pooling needed — taigun is a short-lived CLI tool

### Dependencies

- 003, 004
- 002 (connection details confirmed working)

### Blocks

- 009, 010

### Priority

- High
