from typing import Dict, List, Tuple


_STATUS_TABLES: Dict[str, str] = {
    "story": "projects_userstorystatus",
    "task": "projects_taskstatus",
    "issue": "projects_issuestatus",
    "epic": "projects_epicstatus",
}


class Lister:
    """Read-only queries for listing Taiga entities.

    Accepts an open psycopg2 connection and queries Taiga's schema to
    retrieve projects, epics, and statuses for display in the CLI.
    """

    def __init__(self, conn) -> None:
        self._conn = conn

    def list_projects(self) -> List[Tuple[str, str]]:
        """Return all projects as (name, slug) pairs, ordered by name.

        Returns:
            List of (name, slug) tuples.
        """
        with self._conn.cursor() as cur:
            cur.execute("SELECT name, slug FROM projects_project ORDER BY name")
            return cur.fetchall()

    def list_epics(self, project_id: int) -> List[Tuple[int, str]]:
        """Return all epics in a project as (ref, subject) pairs, ordered by ref.

        Args:
            project_id: Project ID.

        Returns:
            List of (ref, subject) tuples.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT ref, subject FROM epics_epic"
                " WHERE project_id = %s ORDER BY ref",
                (project_id,),
            )

            return cur.fetchall()

    def list_statuses(self, project_id: int) -> Dict[str, List[Tuple[str, bool]]]:
        """Return statuses grouped by ticket type for a project.

        Args:
            project_id: Project ID.

        Returns:
            Dict mapping ticket type ('story', 'task', 'issue', 'epic') to a list
            of (name, is_closed) tuples ordered by the status display order.
        """
        result: Dict[str, List[Tuple[str, bool]]] = {}
        for ticket_type, table in _STATUS_TABLES.items():
            with self._conn.cursor() as cur:
                cur.execute(
                    f'SELECT name, is_closed FROM {table}'
                    f' WHERE project_id = %s ORDER BY "order"',
                    (project_id,),
                )
                result[ticket_type] = cur.fetchall()

        return result
