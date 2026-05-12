"""Factory helpers for integration tests.

Each function takes an open psycopg2 connection and uses taigun's own app code
to set up the state under test. No raw SQL.
"""
from taigun.db.project import ProjectCreator
from taigun.resolver import Resolver


def make_project(conn, name: str = "Test Project", slug: str = "test-project") -> int:
    """Create a Taiga project via taigun's ProjectCreator.

    Args:
        conn: Open psycopg2 connection.
        name: Human-readable project name.
        slug: Project slug.

    Returns:
        Project ID.
    """
    resolver = Resolver(conn)
    creator = ProjectCreator(conn, resolver)
    project_id, _ = creator.create(name, slug, "admin")

    return project_id
