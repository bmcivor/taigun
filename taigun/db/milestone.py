import datetime
import re
from typing import Optional

import psycopg2.extensions

from taigun.models import Milestone
from taigun.resolver import Resolver


class MilestoneWriter:
    """Inserts a Milestone into the Taiga database.

    Must be used within a transaction managed by ConnectionManager.
    """

    def __init__(self, conn: psycopg2.extensions.connection, resolver: Resolver) -> None:
        self._conn = conn
        self._resolver = resolver

    def write(self, milestone: Milestone, acting_user: str) -> int:
        """Insert a milestone and return the inserted row id.

        Args:
            milestone: Populated Milestone model.
            acting_user: Username of the acting user (becomes owner_id).

        Returns:
            Inserted milestone id.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        project_id = self._resolver.resolve_project(milestone.project)

        if milestone.assignee is not None:
            owner_id: Optional[int] = self._resolver.resolve_user(milestone.assignee)
        else:
            owner_id = self._resolver.resolve_user(acting_user)

        slug = _slugify(milestone.subject)
        order = self._next_order(project_id)

        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO milestones_milestone"
                ' (name, slug, estimated_start, estimated_finish,'
                '  created_date, modified_date, closed, "order",'
                '  project_id, owner_id)'
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                " RETURNING id",
                (
                    milestone.subject,
                    slug,
                    milestone.estimated_start,
                    milestone.estimated_finish,
                    now,
                    now,
                    milestone.closed,
                    order,
                    project_id,
                    owner_id,
                ),
            )
            return cur.fetchone()[0]

    def _next_order(self, project_id: int) -> int:
        """Return the next available order value for this project.

        Milestones on the project's board are shown in ascending order. Newly
        created milestones go at the end.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                'SELECT COALESCE(MAX("order"), 0) + 1'
                " FROM milestones_milestone WHERE project_id = %s",
                (project_id,),
            )
            return cur.fetchone()[0]


def _slugify(name: str) -> str:
    """Convert a milestone name into a URL-safe slug.

    Lowercased, non-alphanumeric runs collapsed to a single dash, edges
    trimmed. Matches the convention Taiga uses for project slugs.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "milestone"
