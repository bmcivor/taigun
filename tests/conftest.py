"""Root pytest configuration.

Provides the `real_conn` fixture used by all integration tests. The fixture
opens a psycopg2 connection to the test-db service (configured via the
`TEST_DB_URL` env var) and rolls back any test-specific writes on teardown.

`pythonpath = ["tests"]` in pyproject.toml lets tests import helpers like
`factories` without packages or relative imports.
"""
import os

import psycopg2
import pytest

from taigun.config import Profile
from taigun.db.connection import ConnectionManager


@pytest.fixture
def test_db_profile() -> Profile:
    """Profile pointing at the test-db container, derived from TEST_DB_URL.

    Used by CLI integration tests that go through ConnectionManager and need a
    real Profile to connect with.
    """
    db_url = os.environ.get("TEST_DB_URL")
    if not db_url:
        pytest.skip("TEST_DB_URL not set - integration tests skipped")

    parsed = psycopg2.extensions.parse_dsn(db_url)

    return Profile(
        host=parsed["host"],
        port=int(parsed.get("port", 5432)),
        database=parsed["dbname"],
        username=parsed["user"],
        password=parsed["password"],
        acting_user="admin",
    )


@pytest.fixture
def real_conn():
    """psycopg2 connection to test-db; writes rolled back on teardown.

    Baseline init data (admin user, default project templates) was committed
    by test-db-init before the suite ran, so it persists across tests. Writes
    inside a test accumulate in the open transaction and are rolled back when
    the fixture tears down, so they do not leak between tests.
    """
    db_url = os.environ.get("TEST_DB_URL")
    if not db_url:
        pytest.skip("TEST_DB_URL not set - integration tests skipped")

    conn = psycopg2.connect(db_url)
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


@pytest.fixture
def cli_conn(real_conn, monkeypatch):
    """Route the CLI's ConnectionManager to real_conn so CLI tests share
    state with the test's open transaction (no commit needed).

    Uses ConnectionManager's ``_connection_factory`` seam: the CLI's binding
    of ``taigun.cli.ConnectionManager`` is replaced with a subclass that
    passes a factory returning a savepoint-scoped wrapper around real_conn.

    Each CLI invocation gets its own SAVEPOINT on real_conn:
      - CLI commit()   -> RELEASE SAVEPOINT   (kept inside real_conn's txn)
      - CLI rollback() -> ROLLBACK TO SAVEPOINT  (error path still works)
      - CLI close()    -> no-op   (the fixture owns the connection)

    real_conn's teardown rollback wipes everything at the end of the test,
    so no per-test cleanup is needed.
    """
    counter = {"n": 0}

    class SharedConnWrapper:
        def __init__(self, conn):
            self._conn = conn
            self._sp = None

        def _begin(self):
            self._sp = f"cli_sp_{counter['n']}"
            counter["n"] += 1
            with self._conn.cursor() as cur:
                cur.execute(f"SAVEPOINT {self._sp}")

        def commit(self):
            if self._sp:
                with self._conn.cursor() as cur:
                    cur.execute(f"RELEASE SAVEPOINT {self._sp}")
                self._sp = None

        def rollback(self):
            if self._sp:
                with self._conn.cursor() as cur:
                    cur.execute(f"ROLLBACK TO SAVEPOINT {self._sp}")
                self._sp = None

        def close(self):
            pass

        def __getattr__(self, name):
            return getattr(self._conn, name)

    def shared_factory(*args, **kwargs):
        wrapper = SharedConnWrapper(real_conn)
        wrapper._begin()
        return wrapper

    class SharedConnectionManager(ConnectionManager):
        def __init__(self, config):
            super().__init__(config, _connection_factory=shared_factory)

    monkeypatch.setattr("taigun.cli.ConnectionManager", SharedConnectionManager)

    yield real_conn
