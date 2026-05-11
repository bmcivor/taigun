import datetime
import os
from unittest.mock import MagicMock

import psycopg2
import pytest


FIXED_NOW = datetime.datetime(2024, 1, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
FIXED_ORDER = int(FIXED_NOW.timestamp())


@pytest.fixture
def real_conn():
    """psycopg2 connection to test-db; all writes rolled back on teardown.

    Baseline init data (admin user, default project templates) was committed by
    test-db-init before the test run, so it persists across tests. Test-specific
    writes accumulate in the open transaction and are rolled back at teardown,
    so they don't leak between tests.
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
def mock_conn():
    """psycopg2 connection mock with a cursor that returns (101,) then (42,)
    for successive fetchone() calls — matching the INSERT RETURNING id and
    RefAllocator nextval pattern used by all writers.
    """
    cursor = MagicMock()
    cursor.fetchone.side_effect = [(101,), (42,)]
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor

    return conn


@pytest.fixture
def mock_cursor(mock_conn):
    """The cursor embedded in mock_conn, for direct call inspection."""
    return mock_conn.cursor.return_value.__enter__.return_value
