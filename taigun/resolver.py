import logging
from typing import Optional

from taigun.exceptions import ResolveError


logger = logging.getLogger(__name__)

STATUS_TABLES = {
    "story": "projects_userstorystatus",
    "task": "projects_taskstatus",
    "issue": "projects_issuestatus",
    "epic": "projects_epicstatus",
}

DEFAULT_STATUS_COLUMNS = {
    "story": "default_us_status_id",
    "task": "default_task_status_id",
    "issue": "default_issue_status_id",
    "epic": "default_epic_status_id",
}


class Resolver:
    """Resolves human-readable references to FK IDs for use in DB writes.

    Accepts an open psycopg2 connection and queries Taiga's schema to look
    up IDs for projects, users, statuses, priorities, and other entities.
    Content type IDs are cached for the lifetime of the instance.
    """

    def __init__(self, conn) -> None:
        self._conn = conn
        self._content_type_cache: dict[tuple[str, str], int] = {}

    def resolve_project(self, slug: str) -> int:
        """Look up a project ID by slug.

        Args:
            slug: Project slug string.

        Returns:
            Project ID.

        Raises:
            ResolveError: If no project with that slug exists.
        """
        with self._conn.cursor() as cur:
            cur.execute("SELECT id FROM projects_project WHERE slug = %s", (slug,))
            row = cur.fetchone()

        if row is None:
            raise ResolveError(f"Project '{slug}' not found")

        return row[0]

    def resolve_user(self, username: str) -> int:
        """Look up a user ID by username.

        Args:
            username: Taiga username string.

        Returns:
            User ID.

        Raises:
            ResolveError: If no user with that username exists.
        """
        with self._conn.cursor() as cur:
            cur.execute("SELECT id FROM users_user WHERE username = %s", (username,))
            row = cur.fetchone()

        if row is None:
            raise ResolveError(f"User '{username}' not found")

        return row[0]

    def status_is_closed(self, status_id: int, ticket_type: str) -> bool:
        """Return the ``is_closed`` flag for a resolved status ID.

        Writers that mirror their own row's ``is_closed`` column from the
        status (E12 #56) call this after resolving the status ID. Kept
        separate from ``resolve_status`` so callers that don't need the
        flag pay nothing.
        """
        table = STATUS_TABLES.get(ticket_type)
        if table is None:
            raise ResolveError(f"Unknown ticket type '{ticket_type}'")

        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT is_closed FROM {table} WHERE id = %s",
                (status_id,),
            )
            row = cur.fetchone()

        if row is None:
            raise ResolveError(
                f"Status id {status_id} not found in {table}"
            )

        return row[0]

    def resolve_default_status(self, project_id: int, ticket_type: str) -> int:
        """Look up the default status ID for the given project and ticket type.

        Args:
            project_id: Project ID.
            ticket_type: One of 'story', 'task', 'issue', 'epic'.

        Returns:
            Default status ID.

        Raises:
            ResolveError: If ticket_type is invalid or no default status is found.
        """
        column = DEFAULT_STATUS_COLUMNS.get(ticket_type)
        if column is None:
            raise ResolveError(f"Unknown ticket type '{ticket_type}'")

        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT {column} FROM projects_project WHERE id = %s",
                (project_id,),
            )
            row = cur.fetchone()

        if row is None or row[0] is None:
            raise ResolveError(f"No default status found for project {project_id}")

        return row[0]

    def resolve_status(
        self, project_id: int, name: Optional[str], ticket_type: str
    ) -> int:
        """Look up a status ID by name, falling back to the project default.

        Matching is case-insensitive. If ``name`` is None or no match is
        found, returns the project's default status for the given ticket
        type. A warning is logged only when a name was given but not found —
        symmetric with ``resolve_priority`` / ``resolve_issue_type`` /
        ``resolve_severity`` (see E10 037).

        Args:
            project_id: Project ID.
            name: Status name, or None to use the project default directly.
            ticket_type: One of 'story', 'task', 'issue', 'epic'.

        Returns:
            Status ID.

        Raises:
            ResolveError: If ticket_type is invalid or no default status
                exists for the project.
        """
        table = STATUS_TABLES.get(ticket_type)
        if table is None:
            raise ResolveError(f"Unknown ticket type '{ticket_type}'")

        if name is not None:
            with self._conn.cursor() as cur:
                cur.execute(
                    f"SELECT id FROM {table}"
                    f" WHERE project_id = %s AND LOWER(name) = LOWER(%s)",
                    (project_id, name),
                )
                row = cur.fetchone()

            if row is not None:
                return row[0]

            logger.warning(
                "Status '%s' not found for project %d (%s), falling back to default",
                name, project_id, ticket_type,
            )

        return self.resolve_default_status(project_id, ticket_type)

    def resolve_priority(self, project_id: int, name: Optional[str]) -> int:
        """Look up a priority ID by name, falling back to the project default.

        Matching is case-insensitive. If name is None or no match is found,
        returns the project's default priority. A warning is logged only when
        a name was given but not found.

        Args:
            project_id: Project ID.
            name: Priority name, or None to use the project default directly.

        Returns:
            Priority ID.

        Raises:
            ResolveError: If no match and no default priority exists.
        """
        if name is not None:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM projects_priority"
                    " WHERE project_id = %s AND LOWER(name) = LOWER(%s)",
                    (project_id, name),
                )
                row = cur.fetchone()

            if row is not None:
                return row[0]

            logger.warning(
                "Priority '%s' not found for project %d, falling back to default", name, project_id
            )

        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT default_priority_id FROM projects_project WHERE id = %s",
                (project_id,),
            )
            row = cur.fetchone()

        if row is None or row[0] is None:
            raise ResolveError(f"No default priority found for project {project_id}")

        return row[0]

    def resolve_issue_type(self, project_id: int, name: Optional[str]) -> int:
        """Look up an issue type ID by name, falling back to the project default.

        Matching is case-insensitive. If name is None or no match is found,
        returns the project's default issue type. A warning is logged only when
        a name was given but not found.

        Args:
            project_id: Project ID.
            name: Issue type name, or None to use the project default directly.

        Returns:
            Issue type ID.

        Raises:
            ResolveError: If no match and no default issue type exists.
        """
        if name is not None:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM projects_issuetype"
                    " WHERE project_id = %s AND LOWER(name) = LOWER(%s)",
                    (project_id, name),
                )
                row = cur.fetchone()

            if row is not None:
                return row[0]

            logger.warning(
                "Issue type '%s' not found for project %d, falling back to default",
                name,
                project_id,
            )

        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT default_issue_type_id FROM projects_project WHERE id = %s",
                (project_id,),
            )
            row = cur.fetchone()

        if row is None or row[0] is None:
            raise ResolveError(f"No default issue type found for project {project_id}")

        return row[0]

    def resolve_severity(self, project_id: int, name: Optional[str]) -> int:
        """Look up a severity ID by name, falling back to the project default.

        Matching is case-insensitive. If name is None or no match is found,
        returns the project's default severity. A warning is logged only when
        a name was given but not found.

        Args:
            project_id: Project ID.
            name: Severity name, or None to use the project default directly.

        Returns:
            Severity ID.

        Raises:
            ResolveError: If no match and no default severity exists.
        """
        if name is not None:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM projects_severity"
                    " WHERE project_id = %s AND LOWER(name) = LOWER(%s)",
                    (project_id, name),
                )
                row = cur.fetchone()

            if row is not None:
                return row[0]

            logger.warning(
                "Severity '%s' not found for project %d, falling back to default",
                name,
                project_id,
            )

        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT default_severity_id FROM projects_project WHERE id = %s",
                (project_id,),
            )
            row = cur.fetchone()

        if row is None or row[0] is None:
            raise ResolveError(f"No default severity found for project {project_id}")

        return row[0]

    def resolve_story(self, project_id: int, ref: int) -> int:
        """Look up a user story ID by project-scoped ref number.

        Args:
            project_id: Project ID.
            ref: User story ref number within the project.

        Returns:
            User story ID.

        Raises:
            ResolveError: If no user story with that ref exists.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM userstories_userstory WHERE project_id = %s AND ref = %s",
                (project_id, ref),
            )
            row = cur.fetchone()

        if row is None:
            raise ResolveError(f"Story ref #{ref} not found for project {project_id}")

        return row[0]

    def resolve_epic(self, project_id: int, ref: int) -> int:
        """Look up an epic ID by project-scoped ref number.

        Args:
            project_id: Project ID.
            ref: Epic ref number within the project.

        Returns:
            Epic ID.

        Raises:
            ResolveError: If no epic with that ref exists.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM epics_epic WHERE project_id = %s AND ref = %s",
                (project_id, ref),
            )
            row = cur.fetchone()

        if row is None:
            raise ResolveError(f"Epic ref #{ref} not found for project {project_id}")

        return row[0]

    def resolve_milestone(self, project_id: int, name: str) -> int:
        """Look up a milestone ID by name.

        Args:
            project_id: Project ID.
            name: Milestone name (case-insensitive).

        Returns:
            Milestone ID.

        Raises:
            ResolveError: If the milestone is not found.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM milestones_milestone"
                " WHERE project_id = %s AND LOWER(name) = LOWER(%s)",
                (project_id, name),
            )
            row = cur.fetchone()

        if row is None:
            raise ResolveError(f"Milestone '{name}' not found for project {project_id}")

        return row[0]

    def resolve_content_type(self, app_label: str, model: str) -> int:
        """Look up a Django content type ID, caching results for the session.

        Args:
            app_label: Django app label (e.g. 'epics').
            model: Model name in lowercase (e.g. 'epic').

        Returns:
            Content type ID.

        Raises:
            ResolveError: If the content type is not found.
        """
        key = (app_label, model)

        if key in self._content_type_cache:
            return self._content_type_cache[key]

        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM django_content_type WHERE app_label = %s AND model = %s",
                (app_label, model),
            )
            row = cur.fetchone()

        if row is None:
            raise ResolveError(f"Content type '{app_label}.{model}' not found")

        self._content_type_cache[key] = row[0]

        return row[0]
