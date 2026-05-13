"""Factory helpers for integration tests.

Each function takes an open psycopg2 connection. Prefer using taigun's own
app code (ProjectCreator etc.) over raw SQL. Raw SQL is permitted only as
a stop-gap for entities taigun does not yet write (e.g. milestones).
"""
import datetime

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


def make_milestone(conn, project_id: int, name: str = "Sprint 1") -> int:
    """Insert a milestone for the given project.

    Raw SQL because taigun does not have a MilestoneWriter. Used by integration
    tests that need a milestone to resolve.

    Args:
        conn: Open psycopg2 connection.
        project_id: Project the milestone belongs to.
        name: Milestone name (also used as the slug after lowercasing).

    Returns:
        Milestone ID.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    today = now.date()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO milestones_milestone"
            ' (name, slug, estimated_start, estimated_finish,'
            '  created_date, modified_date, closed, "order", project_id)'
            " VALUES (%s, %s, %s, %s, %s, %s, false, 1, %s)"
            " RETURNING id",
            (
                name,
                name.lower().replace(" ", "-"),
                today,
                today + datetime.timedelta(days=14),
                now,
                now,
                project_id,
            ),
        )
        return cur.fetchone()[0]
