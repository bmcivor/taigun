---
type: story
project: taigun
status: Done
---

## 26. Replace cli_conn monkeypatch with a proper test seam

**As a** taigun developer
**I want** the CLI test fixture to share state with the test transaction via dependency injection, not by patching psycopg2.connect
**So that** the test scaffolding doesn't reach into a third-party library at module level

**Priority:** Medium

### Context

The `cli_conn` fixture in `tests/conftest.py` calls
`monkeypatch.setattr("taigun.db.connection.psycopg2.connect", fake_connect)`. This
works, but patches `psycopg2.connect` globally for the duration of the test — anything
else in the process that calls `psycopg2.connect` is intercepted too.

The cleaner pattern is constructor injection on `ConnectionManager`:

```python
class ConnectionManager:
    def __init__(self, config: Profile, *, _connection_factory=None) -> None:
        self._config = config
        self._connect = _connection_factory or psycopg2.connect
```

The CLI keeps calling `ConnectionManager(config)` — no change to call sites. Tests
patch `taigun.cli.ConnectionManager` (matching the existing pattern used for
`ConfigManager`) to install one with `_connection_factory=test_shared_conn_factory`.

### Acceptance criteria

- `ConnectionManager.__init__` takes an optional `_connection_factory` keyword-only
  argument that defaults to `psycopg2.connect`
- `tests/conftest.py::cli_conn` is rewritten to patch `taigun.cli.ConnectionManager`
  with a wrapper that injects the test connection — no `psycopg2.connect`
  monkeypatching anywhere in the test suite
- The savepoint / RELEASE / ROLLBACK TO semantics for sharing state across the
  test transaction are preserved
- All 180 existing tests still pass
- Production code path is unchanged in behaviour (the new constructor argument is
  underscore-prefixed and only used by tests)

### Dependencies

- v1.0 released
