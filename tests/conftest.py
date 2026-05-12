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
