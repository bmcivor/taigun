import psycopg2.errors


class RefAllocator:
    """Allocates a project-scoped ref number for a newly inserted ticket.

    Calls the per-project Postgres sequence to get the next ref, then
    inserts the corresponding row into ``references_reference``. Must be
    called within the same transaction as the ticket insert.
    """

    def __init__(self, conn) -> None:
        self._conn = conn

    def allocate(self, project_id: int, object_id: int, content_type_id: int) -> int:
        """Get the next ref for a project and record it in references_reference.

        Args:
            project_id: Project ID.
            object_id: ID of the newly inserted ticket row.
            content_type_id: Django content type ID for the ticket model.

        Returns:
            The allocated ref number.

        Raises:
            SystemExit: If the sequence for the project does not exist.
        """
        sequence = f"references_project{project_id}"

        try:
            with self._conn.cursor() as cur:
                cur.execute(f"SELECT nextval('{sequence}')")
                ref = cur.fetchone()[0]
        except psycopg2.errors.UndefinedTable:
            raise SystemExit(f"Ref sequence for project {project_id} does not exist")

        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO references_reference (ref, object_id, content_type_id, project_id)"
                " VALUES (%s, %s, %s, %s)",
                (ref, object_id, content_type_id, project_id),
            )

        return ref
