import datetime
import re
from typing import Optional

import psycopg2.extensions

from taigun.db.update_helpers import (
    check_taiga_conflict,
    parse_taiga_timestamp,
)
from taigun.exceptions import (
    MilestoneConflictError,
    MilestoneMissingError,
)
from taigun.models import Milestone
from taigun.resolver import Resolver


class MilestoneWriter:
    """Inserts a Milestone into the Taiga database.

    Must be used within a transaction managed by ConnectionManager.
    """

    def __init__(
        self, conn: psycopg2.extensions.connection, resolver: Resolver
    ) -> None:
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
                " (name, slug, estimated_start, estimated_finish,"
                '  created_date, modified_date, closed, "order",'
                "  project_id, owner_id)"
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

    def update(
        self,
        milestone: Milestone,
        milestone_id: int,
        metadata_keys: set,
        acting_user: str,
        last_pushed_at: str,
        ignore_conflict: bool = False,
    ) -> None:
        """Update an existing milestone from the parsed model.

        Same semantics as the ticket writers' ``update()`` methods (see
        ``StoryWriter.update``): fetch by (project, id), refuse if the row is
        gone, raise on modified_date drift, raise if a previously-set field
        is silently dropped, then UPDATE.

        Args:
            milestone: Re-parsed Milestone model.
            milestone_id: Sidecar-recorded milestones_milestone.id (the
                sidecar stores this in its ``ref`` field for milestones).
            metadata_keys: Frontmatter keys present in the source — used to
                distinguish "omitted" from "explicitly null".
            acting_user: Username driving the update.
            last_pushed_at: ISO timestamp from the sidecar.
            ignore_conflict: If True, skip the modified_date drift check
                (caller has already prompted the user).

        Raises:
            MilestoneMissingError: The id does not exist in this project.
            MilestoneConflictError: Row was modified after ``last_pushed_at``.
        """
        project_id = self._resolver.resolve_project(milestone.project)

        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id, modified_date"
                " FROM milestones_milestone WHERE project_id = %s AND id = %s",
                (project_id, milestone_id),
            )
            row = cur.fetchone()

        if row is None:
            raise MilestoneMissingError(
                f"milestone id {milestone_id} not found in project "
                f"'{milestone.project}'"
            )

        object_id, taiga_modified = row

        if not ignore_conflict:
            check_taiga_conflict(
                taiga_modified,
                parse_taiga_timestamp(last_pushed_at),
                conflict_exception=MilestoneConflictError,
            )

        if milestone.assignee is not None:
            owner_id: Optional[int] = self._resolver.resolve_user(milestone.assignee)
        else:
            owner_id = self._resolver.resolve_user(acting_user)

        slug = _slugify(milestone.subject)
        now = datetime.datetime.now(datetime.timezone.utc)

        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE milestones_milestone"
                " SET name = %s, slug = %s,"
                "     estimated_start = %s, estimated_finish = %s,"
                "     closed = %s, owner_id = %s, modified_date = %s"
                " WHERE id = %s",
                (
                    milestone.subject,
                    slug,
                    milestone.estimated_start,
                    milestone.estimated_finish,
                    milestone.closed,
                    owner_id,
                    now,
                    object_id,
                ),
            )

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
