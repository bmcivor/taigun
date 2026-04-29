import datetime
from typing import Optional

from taigun.db.ref import RefAllocator
from taigun.models import Story


class StoryWriter:
    """Inserts a Story and all related rows into the Taiga database.

    Must be used within a transaction managed by ConnectionManager.
    """

    def __init__(self, conn, resolver) -> None:
        self._conn = conn
        self._resolver = resolver

    def write(self, story: Story, acting_user: str) -> int:
        """Insert a story and return the allocated ref number.

        Resolves all FK references, inserts into userstories_userstory,
        allocates a project-scoped ref, and writes any M2M or related rows.

        Args:
            story: Populated Story model.
            acting_user: Username of the acting user (becomes owner_id).

        Returns:
            Allocated ref number.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        order = int(now.timestamp())

        project_id = self._resolver.resolve_project(story.project)
        owner_id = self._resolver.resolve_user(acting_user)

        if story.status is not None:
            status_id = self._resolver.resolve_status(project_id, story.status, "story")
        else:
            status_id = self._resolver.resolve_default_status(project_id, "story")

        priority_id = self._resolver.resolve_priority(project_id, story.priority)

        assigned_to_id: Optional[int] = None
        if story.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(story.assignee)

        milestone_id: Optional[int] = None
        if story.milestone is not None:
            milestone_id = self._resolver.resolve_milestone(project_id, story.milestone)

        content_type_id = self._resolver.resolve_content_type("userstories", "userstory")

        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO userstories_userstory"
                " (subject, description, project_id, status_id, priority_id, owner_id,"
                "  assigned_to_id, milestone_id, ref, created_date, modified_date, version,"
                "  backlog_order, sprint_order, kanban_order)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 1, %s, %s, %s)"
                " RETURNING id",
                (
                    story.subject,
                    story.description,
                    project_id,
                    status_id,
                    priority_id,
                    owner_id,
                    assigned_to_id,
                    milestone_id,
                    now,
                    now,
                    order,
                    order,
                    order,
                ),
            )
            object_id = cur.fetchone()[0]

        ref = RefAllocator(self._conn).allocate(project_id, object_id, content_type_id)

        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE userstories_userstory SET ref = %s WHERE id = %s",
                (ref, object_id),
            )

        if story.assignee is not None:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO userstories_userstory_assigned_users"
                    " (userstory_id, user_id)"
                    " VALUES (%s, %s)",
                    (object_id, assigned_to_id),
                )

        if story.epic is not None:
            epic_id = self._resolver.resolve_epic(project_id, story.epic)
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO epics_relateduserstory (epic_id, user_story_id)"
                    " VALUES (%s, %s)",
                    (epic_id, object_id),
                )

        return ref
