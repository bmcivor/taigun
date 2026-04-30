import datetime
import random
from typing import Optional

from taigun.db.ref import RefAllocator
from taigun.models import Epic


def _random_color() -> str:
    return f"#{random.randint(0, 0xFFFFFF):06x}"


class EpicWriter:
    """Inserts an Epic and all related rows into the Taiga database.

    Must be used within a transaction managed by ConnectionManager.
    """

    def __init__(self, conn, resolver) -> None:
        self._conn = conn
        self._resolver = resolver

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
        now = datetime.datetime.now(datetime.timezone.utc)
        order = int(now.timestamp())

        project_id = self._resolver.resolve_project(epic.project)
        owner_id = self._resolver.resolve_user(acting_user)

        if epic.status is not None:
            status_id = self._resolver.resolve_status(project_id, epic.status, "epic")
        else:
            status_id = self._resolver.resolve_default_status(project_id, "epic")

        color = epic.color if epic.color is not None else _random_color()

        assigned_to_id: Optional[int] = None
        if epic.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(epic.assignee)

        content_type_id = self._resolver.resolve_content_type("epics", "epic")

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

        ref = RefAllocator(self._conn).allocate(project_id, object_id, content_type_id)

        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE epics_epic SET ref = %s WHERE id = %s",
                (ref, object_id),
            )

        return ref
