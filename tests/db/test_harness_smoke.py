"""Smoke tests for the integration test harness.

Confirms that `real_conn` yields a working psycopg2 connection to `test-db` and
that baseline data populated by `test-db-init` is readable.
"""
from .factories import default_admin_user_id


def test_real_conn_yields_working_connection(real_conn):
    """Setup: real_conn fixture; test-db must be reachable via TEST_DB_URL.
    Expectations: cursor executes a trivial SELECT and returns the expected row.
    """
    with real_conn.cursor() as cur:
        cur.execute("SELECT 1")
        assert cur.fetchone() == (1,)


def test_baseline_admin_user_present(real_conn):
    """Setup: test-db-init has run before tests, creating the admin user.
    Expectations: default_admin_user_id returns a positive integer id.
    """
    admin_id = default_admin_user_id(real_conn)

    assert isinstance(admin_id, int)
    assert admin_id > 0


def test_baseline_project_templates_present(real_conn):
    """Setup: test-db-init ran `loaddata initial_project_templates`.
    Expectations: at least one row in projects_projecttemplate.
    """
    with real_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM projects_projecttemplate")
        count = cur.fetchone()[0]

    assert count >= 1
