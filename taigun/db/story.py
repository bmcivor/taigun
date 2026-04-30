from typing import Optional

from taigun.db.base import BaseWriter
from taigun.models import Story


class StoryWriter(BaseWriter):
    """Inserts a Story and all related rows into the Taiga database.

    Must be used within a transaction managed by ConnectionManager.
    """

    _ticket_type = "story"
    _content_type = ("userstories", "userstory")
    _table = "userstories_userstory"

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
        project_id, owner_id, status_id, now = self._resolve_common(story, acting_user)
        order = int(now.timestamp())
        priority_id = self._resolver.resolve_priority(project_id, story.priority)

        assigned_to_id: Optional[int] = None
        if story.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(story.assignee)

        milestone_id: Optional[int] = None
        if story.milestone is not None:
            milestone_id = self._resolver.resolve_milestone(project_id, story.milestone)

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

        ref = self._allocate_and_set_ref(project_id, object_id)

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
