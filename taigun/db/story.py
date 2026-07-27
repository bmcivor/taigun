import datetime
from typing import Optional

from taigun.db.base import BaseWriter
from taigun.db.update_helpers import check_field_cleared
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
        is_closed = self._resolver.status_is_closed(status_id, self._ticket_type)
        order = int(now.timestamp())

        assigned_to_id: Optional[int] = None
        if story.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(story.assignee)

        milestone_id: Optional[int] = None
        if story.milestone is not None:
            milestone_id = self._resolver.resolve_milestone(project_id, story.milestone)

        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO userstories_userstory"
                " (subject, description, project_id, status_id, owner_id,"
                "  assigned_to_id, milestone_id, ref, created_date, modified_date, version,"
                "  backlog_order, sprint_order, kanban_order,"
                "  is_blocked, blocked_note, is_closed, tags,"
                "  client_requirement, team_requirement, due_date_reason)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 1, %s, %s, %s,"
                "         false, '', %s, %s, false, false, '')"
                " RETURNING id",
                (
                    story.subject,
                    story.description,
                    project_id,
                    status_id,
                    owner_id,
                    assigned_to_id,
                    milestone_id,
                    now,
                    now,
                    order,
                    order,
                    order,
                    is_closed,
                    story.tags or [],
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
                    'INSERT INTO epics_relateduserstory (epic_id, user_story_id, "order")'
                    " VALUES (%s, %s, %s)",
                    (epic_id, object_id, order),
                )

        return ref

    def update(
        self,
        story: Story,
        ref: int,
        metadata_keys: set,
        acting_user: str,
        last_pushed_at: str,
        ignore_conflict: bool = False,
    ) -> None:
        """Update an existing story from the parsed model.

        Args:
            story: Populated Story model from the (re-)parsed source file.
            ref: Taiga ref of the row being updated.
            metadata_keys: Set of frontmatter keys explicitly present in the
                source — used to distinguish "omitted" from "explicitly null"
                per ADR-004's clear semantics.
            acting_user: Username driving the update (used for the row's
                modified_date; no separate modified_by column exists on
                userstories_userstory).
            last_pushed_at: ISO timestamp from the sidecar for conflict
                detection.
            ignore_conflict: If True, skip the modified_date drift check
                (caller has already prompted the user).

        Raises:
            TicketMissingError: The ref does not exist on this project.
            TicketConflictError: Taiga's row was modified after last_pushed_at.
            FieldClearedError: A previously-set field was omitted without an
                explicit null.
        """
        project_id, object_id, (current_assigned_to, current_milestone) = (
            self._fetch_for_update(
                story.project,
                ref,
                ["assigned_to_id", "milestone_id"],
                last_pushed_at,
                ignore_conflict,
            )
        )

        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT epic_id FROM epics_relateduserstory WHERE user_story_id = %s",
                (object_id,),
            )
            current_epic = cur.fetchone()

        check_field_cleared("assignee", metadata_keys, current_assigned_to)
        check_field_cleared("milestone", metadata_keys, current_milestone)
        check_field_cleared("epic", metadata_keys, current_epic)

        status_id = self._resolve_status(project_id, story.status)
        is_closed = self._resolver.status_is_closed(status_id, self._ticket_type)

        assigned_to_id: Optional[int] = None
        if story.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(story.assignee)

        milestone_id: Optional[int] = None
        if story.milestone is not None:
            milestone_id = self._resolver.resolve_milestone(project_id, story.milestone)

        epic_id: Optional[int] = None
        if story.epic is not None:
            epic_id = self._resolver.resolve_epic(project_id, story.epic)

        now = datetime.datetime.now(datetime.timezone.utc)

        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE userstories_userstory"
                " SET subject = %s, description = %s, status_id = %s,"
                "     is_closed = %s,"
                "     assigned_to_id = %s, milestone_id = %s, tags = %s,"
                "     modified_date = %s, version = version + 1"
                " WHERE id = %s",
                (
                    story.subject,
                    story.description,
                    status_id,
                    is_closed,
                    assigned_to_id,
                    milestone_id,
                    story.tags or [],
                    now,
                    object_id,
                ),
            )

            cur.execute(
                "DELETE FROM userstories_userstory_assigned_users"
                " WHERE userstory_id = %s",
                (object_id,),
            )

            if assigned_to_id is not None:
                cur.execute(
                    "INSERT INTO userstories_userstory_assigned_users"
                    " (userstory_id, user_id) VALUES (%s, %s)",
                    (object_id, assigned_to_id),
                )

            cur.execute(
                "DELETE FROM epics_relateduserstory WHERE user_story_id = %s",
                (object_id,),
            )

            if epic_id is not None:
                cur.execute(
                    'INSERT INTO epics_relateduserstory'
                    ' (epic_id, user_story_id, "order") VALUES (%s, %s, %s)',
                    (epic_id, object_id, int(now.timestamp())),
                )
