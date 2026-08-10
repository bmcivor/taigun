"""Smoke tests for the integration test harness.

Confirm that `real_conn` is reachable and that baseline data populated by
`test-db-init` is queryable via taigun's app code (no raw SQL).
"""

from taigun.db.lister import Lister
from taigun.resolver import Resolver


def test_real_conn_resolves_admin_user(real_conn):
    """Setup: test-db-init has created the admin user.
    Expectations: Resolver.resolve_user('admin') returns a positive id.
    """
    admin_id = Resolver(real_conn).resolve_user("admin")

    assert isinstance(admin_id, int) and admin_id > 0


def test_baseline_has_no_projects_yet(real_conn):
    """Setup: test-db-init does not create any projects (only schema + templates).
    Expectations: Lister.list_projects returns an empty list.
    """
    projects = Lister(real_conn).list_projects()

    assert projects == []
