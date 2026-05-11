"""Factory helpers for integration tests.

Each function takes an open psycopg2 connection. Reads pull baseline data
populated by test-db-init; writes go through direct SQL so factories remain
reliable even if taigun's writers have bugs (the very thing under test).

Writes are NOT committed - the `real_conn` fixture rolls back on teardown.
"""


def default_admin_user_id(conn) -> int:
    """Return the admin user id created by test-db-init.

    Raises:
        RuntimeError: If the admin user is not present (test-db-init didn't run
            or the harness is misconfigured).
    """
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users_user WHERE username = %s", ("admin",))
        row = cur.fetchone()

    if row is None:
        raise RuntimeError(
            "admin user not present in test-db; test-db-init must run before tests"
        )

    return row[0]
