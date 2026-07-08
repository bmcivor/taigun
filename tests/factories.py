"""Factory helpers for integration tests.

Each function takes an open psycopg2 connection and uses taigun's own app code
(ProjectCreator, MilestoneWriter, etc.) to set up the state under test.
"""
import datetime

import psycopg2.extensions

from taigun.db.milestone import MilestoneWriter
from taigun.db.project import ProjectCreator
from taigun.models import Milestone
from taigun.resolver import Resolver


def make_project(
    conn: psycopg2.extensions.connection,
    name: str = "Test Project",
    slug: str = "test-project",
) -> int:
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


def make_milestone(
    conn: psycopg2.extensions.connection,
    project_id: int,
    name: str = "Sprint 1",
) -> int:
    """Create a milestone for the given project via taigun's MilestoneWriter.

    Args:
        conn: Open psycopg2 connection.
        project_id: Project the milestone belongs to (used to resolve the slug
            back for the writer's project field).
        name: Milestone name.

    Returns:
        Milestone ID.
    """
    resolver = Resolver(conn)
    project_slug = _project_slug(conn, project_id)
    today = datetime.date.today()

    milestone = Milestone(
        project=project_slug,
        subject=name,
        estimated_start=today,
        estimated_finish=today + datetime.timedelta(days=14),
    )
    return MilestoneWriter(conn, resolver).write(milestone, "admin")


def _project_slug(conn: psycopg2.extensions.connection, project_id: int) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT slug FROM projects_project WHERE id = %s", (project_id,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"No project with id {project_id}")
        return row[0]
