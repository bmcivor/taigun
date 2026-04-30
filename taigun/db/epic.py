import random
from typing import Optional

from taigun.db.base import BaseWriter
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
                "  color, assigned_to_id, ref, created_date, modified_date, version, epics_order)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 1, %s)"
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
                ),
            )
            object_id = cur.fetchone()[0]

        return self._allocate_and_set_ref(project_id, object_id)
