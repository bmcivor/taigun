import json
from typing import Tuple

from taigun.exceptions import ResolveError


class ProjectCreator:
    """Creates a new Taiga project with the data Taiga's signals normally produce.

    Reads the default ProjectTemplate, materialises its status/priority/severity/
    issue-type definitions into per-project rows, sets the project's default FKs,
    creates the per-project ref sequence, and inserts an admin membership for the
    acting user.

    Must be used within a transaction managed by ConnectionManager.
    """

    def __init__(self, conn, resolver) -> None:
        self._conn = conn
        self._resolver = resolver

    def create(self, name: str, slug: str, acting_user: str) -> Tuple[int, str]:
        """Create a new Taiga project and return its (id, slug).

        Args:
            name: Human-readable project name.
            slug: URL slug for the project.
            acting_user: Username of the user who will be the project owner.

        Returns:
            Tuple of (project_id, slug).

        Raises:
            ResolveError: If acting_user does not exist, or no default template found.
            ProjectExistsError: If a project with the given slug already exists.
        """
        owner_id = self._resolver.resolve_user(acting_user)
        self._guard_slug_unique(slug)
        template = self._load_default_template()

        project_id = self._insert_project(name, slug, owner_id, template["id"])
        self._materialise_statuses(project_id, template)
        self._materialise_lookups(project_id, template)
        self._set_project_defaults(project_id, template)
        self._create_ref_sequence(project_id)
        self._insert_owner_membership(project_id, owner_id, template)

        return project_id, slug

    def _guard_slug_unique(self, slug: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute("SELECT 1 FROM projects_project WHERE slug = %s", (slug,))
            if cur.fetchone() is not None:
                raise ProjectExistsError(f"Project with slug '{slug}' already exists")

    def _load_default_template(self) -> dict:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id, us_statuses, task_statuses, issue_statuses, epic_statuses,"
                " priorities, severities, issue_types, roles, default_options"
                " FROM projects_projecttemplate"
                " ORDER BY id LIMIT 1"
            )
            row = cur.fetchone()

        if row is None:
            raise ResolveError("No ProjectTemplate found in the database")

        return {
            "id": row[0],
            "us_statuses": _as_list(row[1]),
            "task_statuses": _as_list(row[2]),
            "issue_statuses": _as_list(row[3]),
            "epic_statuses": _as_list(row[4]),
            "priorities": _as_list(row[5]),
            "severities": _as_list(row[6]),
            "issue_types": _as_list(row[7]),
            "roles": _as_list(row[8]),
            "default_options": _as_dict(row[9]),
        }

    def _insert_project(self, name: str, slug: str, owner_id: int, template_id: int) -> int:
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO projects_project (name, slug, owner_id, creation_template_id)"
                " VALUES (%s, %s, %s, %s) RETURNING id",
                (name, slug, owner_id, template_id),
            )
            return cur.fetchone()[0]

    def _materialise_statuses(self, project_id: int, template: dict) -> None:
        for entries, table in (
            (template["us_statuses"], "projects_userstorystatus"),
            (template["task_statuses"], "projects_taskstatus"),
            (template["issue_statuses"], "projects_issuestatus"),
            (template["epic_statuses"], "projects_epicstatus"),
        ):
            for entry in entries:
                self._insert_status(table, project_id, entry)

    def _insert_status(self, table: str, project_id: int, entry: dict) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {table}"
                f" (project_id, name, slug, color, \"order\", is_closed)"
                f" VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    project_id,
                    entry["name"],
                    entry["slug"],
                    entry.get("color", "#999999"),
                    entry.get("order", 1),
                    entry.get("is_closed", False),
                ),
            )

    def _materialise_lookups(self, project_id: int, template: dict) -> None:
        for entries, table in (
            (template["priorities"], "projects_priority"),
            (template["severities"], "projects_severity"),
            (template["issue_types"], "projects_issuetype"),
        ):
            for entry in entries:
                self._insert_lookup(table, project_id, entry)

    def _insert_lookup(self, table: str, project_id: int, entry: dict) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {table}"
                f" (project_id, name, color, \"order\")"
                f" VALUES (%s, %s, %s, %s)",
                (
                    project_id,
                    entry["name"],
                    entry.get("color", "#999999"),
                    entry.get("order", 1),
                ),
            )

    def _set_project_defaults(self, project_id: int, template: dict) -> None:
        defaults = template["default_options"]
        mapping = (
            ("default_us_status_id", "projects_userstorystatus", defaults.get("us_status")),
            ("default_task_status_id", "projects_taskstatus", defaults.get("task_status")),
            ("default_issue_status_id", "projects_issuestatus", defaults.get("issue_status")),
            ("default_epic_status_id", "projects_epicstatus", defaults.get("epic_status")),
            ("default_priority_id", "projects_priority", defaults.get("priority")),
            ("default_severity_id", "projects_severity", defaults.get("severity")),
            ("default_issue_type_id", "projects_issuetype", defaults.get("issue_type")),
        )
        for column, table, name in mapping:
            if name is None:
                continue
            target_id = self._lookup_id_by_name(table, project_id, name)
            with self._conn.cursor() as cur:
                cur.execute(
                    f"UPDATE projects_project SET {column} = %s WHERE id = %s",
                    (target_id, project_id),
                )

    def _lookup_id_by_name(self, table: str, project_id: int, name: str) -> int:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT id FROM {table} WHERE project_id = %s AND name = %s",
                (project_id, name),
            )
            row = cur.fetchone()

        if row is None:
            raise ResolveError(f"Default '{name}' not found in {table} for project {project_id}")

        return row[0]

    def _create_ref_sequence(self, project_id: int) -> None:
        with self._conn.cursor() as cur:
            cur.execute(f"CREATE SEQUENCE references_project{project_id} START WITH 1")

    def _insert_owner_membership(self, project_id: int, owner_id: int, template: dict) -> None:
        admin_role = next(
            (r for r in template["roles"] if r.get("name", "").lower() == "admin"),
            template["roles"][0] if template["roles"] else None,
        )
        if admin_role is None:
            raise ResolveError("No roles defined in template, cannot create owner membership")

        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users_role WHERE project_id = %s AND name = %s",
                (project_id, admin_role["name"]),
            )
            row = cur.fetchone()

        if row is None:
            self._insert_role(project_id, admin_role)
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM users_role WHERE project_id = %s AND name = %s",
                    (project_id, admin_role["name"]),
                )
                row = cur.fetchone()

        role_id = row[0]

        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO projects_membership"
                " (project_id, user_id, role_id, is_admin, created_at)"
                " VALUES (%s, %s, %s, true, NOW())",
                (project_id, owner_id, role_id),
            )

    def _insert_role(self, project_id: int, role: dict) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users_role (project_id, name, slug, \"order\", computable)"
                " VALUES (%s, %s, %s, %s, %s)",
                (
                    project_id,
                    role["name"],
                    role.get("slug", role["name"].lower()),
                    role.get("order", 1),
                    role.get("computable", True),
                ),
            )


class ProjectExistsError(Exception):
    """Raised when attempting to create a project with a slug that already exists."""


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, str):
        return json.loads(value)
    return value


def _as_dict(value) -> dict:
    if value is None:
        return {}
    if isinstance(value, str):
        return json.loads(value)
    return value
