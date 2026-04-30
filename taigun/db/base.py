import datetime
from abc import ABC, abstractmethod

from taigun.db.ref import RefAllocator


class BaseWriter(ABC):
    """Shared base for all ticket writers.

    Subclasses declare _ticket_type, _content_type, and _table as class
    attributes, and implement write() with the type-specific INSERT logic.
    """

    _ticket_type: str
    _content_type: tuple[str, str]
    _table: str

    def __init__(self, conn, resolver) -> None:
        self._conn = conn
        self._resolver = resolver

    def _resolve_common(self, ticket, acting_user: str) -> tuple[int, int, int, datetime.datetime]:
        """Resolve the fields common to every ticket type.

        Args:
            ticket: Any ticket model (must have .project and .status attributes).
            acting_user: Username of the acting user (becomes owner_id).

        Returns:
            Tuple of (project_id, owner_id, status_id, now).
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        project_id = self._resolver.resolve_project(ticket.project)
        owner_id = self._resolver.resolve_user(acting_user)
        status_id = self._resolve_status(project_id, ticket.status)
        return project_id, owner_id, status_id, now

    def _resolve_status(self, project_id: int, status: str | None) -> int:
        """Resolve status ID, falling back to the project default if not set.

        Args:
            project_id: Project ID.
            status: Status name, or None to use the default.

        Returns:
            Status ID.
        """
        if status is not None:
            return self._resolver.resolve_status(project_id, status, self._ticket_type)
        return self._resolver.resolve_default_status(project_id, self._ticket_type)

    def _allocate_and_set_ref(self, project_id: int, object_id: int) -> int:
        """Allocate a project-scoped ref and write it back to the inserted row.

        Args:
            project_id: Project ID.
            object_id: ID of the newly inserted ticket row.

        Returns:
            Allocated ref number.
        """
        content_type_id = self._resolver.resolve_content_type(*self._content_type)
        ref = RefAllocator(self._conn).allocate(project_id, object_id, content_type_id)

        with self._conn.cursor() as cur:
            cur.execute(
                f"UPDATE {self._table} SET ref = %s WHERE id = %s",
                (ref, object_id),
            )

        return ref

    @abstractmethod
    def write(self, ticket, acting_user: str) -> int:
        """Insert a ticket and return the allocated ref number.

        Args:
            ticket: Populated ticket model.
            acting_user: Username of the acting user (becomes owner_id).

        Returns:
            Allocated ref number.
        """
