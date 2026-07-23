import datetime
import random
from typing import Optional

from taigun.db.base import BaseWriter
from taigun.db.update_helpers import check_field_cleared
from taigun.models import Epic


def _random_color() -> str:
    return f"#{random.randint(0, 0xFFFFFF):06x}"


class EpicWriter(BaseWriter):
    """Inserts an Epic and all related rows into the Taiga database.

    Must be used within a transaction managed by ConnectionManager.
    """

    _ticket_type = "epic"
    _content_type = ("epics", "epic")
    _table = "epics_epic"

    def write(self, epic: Epic, acting_user: str) -> int:
        """Insert an epic and return the allocated ref number.

        Resolves all FK references, inserts into epics_epic,
        and allocates a project-scoped ref.

        Args:
            epic: Populated Epic model.
            acting_user: Username of the acting user (becomes owner_id).

        Returns:
            Allocated ref number.
        """
        project_id, owner_id, status_id, now = self._resolve_common(epic, acting_user)
        order = int(now.timestamp())
        color = epic.color if epic.color is not None else _random_color()

        assigned_to_id: Optional[int] = None
        if epic.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(epic.assignee)

        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO epics_epic"
                " (subject, description, project_id, status_id, owner_id,"
                "  color, assigned_to_id, ref, created_date, modified_date, version, epics_order,"
                "  is_blocked, blocked_note, tags, client_requirement, team_requirement)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 1, %s,"
                "         false, '', %s, false, false)"
                " RETURNING id",
                (
                    epic.subject,
                    epic.description,
                    project_id,
                    status_id,
                    owner_id,
                    color,
                    assigned_to_id,
                    now,
                    now,
                    order,
                    epic.tags or [],
                ),
            )
            object_id = cur.fetchone()[0]

        return self._allocate_and_set_ref(project_id, object_id)

    def update(
        self,
        epic: Epic,
        ref: int,
        metadata_keys: set,
        acting_user: str,
        last_pushed_at: str,
        ignore_conflict: bool = False,
    ) -> None:
        """Update an existing epic from the parsed model.

        Follows the same semantics as ``StoryWriter.update`` — see that method
        for the field-clear / conflict / missing-ticket rules. Epic keeps its
        original ``color`` unless the source explicitly sets one.
        """
        project_id, object_id, (current_assigned_to, current_color) = (
            self._fetch_for_update(
                epic.project,
                ref,
                ["assigned_to_id", "color"],
                last_pushed_at,
                ignore_conflict,
            )
        )

        check_field_cleared("assignee", metadata_keys, current_assigned_to)

        status_id = self._resolve_status(project_id, epic.status)

        assigned_to_id: Optional[int] = None
        if epic.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(epic.assignee)

        color = epic.color if epic.color is not None else current_color

        now = datetime.datetime.now(datetime.timezone.utc)

        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE epics_epic"
                " SET subject = %s, description = %s, status_id = %s,"
                "     assigned_to_id = %s, color = %s, tags = %s,"
                "     modified_date = %s, version = version + 1"
                " WHERE id = %s",
                (
                    epic.subject,
                    epic.description,
                    status_id,
                    assigned_to_id,
                    color,
                    epic.tags or [],
                    now,
                    object_id,
                ),
            )
