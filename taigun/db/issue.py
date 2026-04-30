import datetime
from typing import Optional

from taigun.db.ref import RefAllocator
from taigun.models import Issue


class IssueWriter:
    """Inserts an Issue and all related rows into the Taiga database.

    Must be used within a transaction managed by ConnectionManager.
    """

    def __init__(self, conn, resolver) -> None:
        self._conn = conn
        self._resolver = resolver

    def write(self, issue: Issue, acting_user: str) -> int:
        """Insert an issue and return the allocated ref number.

        Resolves all FK references, inserts into issues_issue,
        allocates a project-scoped ref, and writes any optional related rows.

        Args:
            issue: Populated Issue model.
            acting_user: Username of the acting user (becomes owner_id).

        Returns:
            Allocated ref number.
        """
        now = datetime.datetime.now(datetime.timezone.utc)

        project_id = self._resolver.resolve_project(issue.project)
        owner_id = self._resolver.resolve_user(acting_user)

        if issue.status is not None:
            status_id = self._resolver.resolve_status(project_id, issue.status, "issue")
        else:
            status_id = self._resolver.resolve_default_status(project_id, "issue")

        priority_id = self._resolver.resolve_priority(project_id, issue.priority)
        type_id = self._resolver.resolve_issue_type(project_id, issue.issue_type)
        severity_id = self._resolver.resolve_severity(project_id, issue.severity)

        assigned_to_id: Optional[int] = None
        if issue.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(issue.assignee)

        milestone_id: Optional[int] = None
        if issue.milestone is not None:
            milestone_id = self._resolver.resolve_milestone(project_id, issue.milestone)

        content_type_id = self._resolver.resolve_content_type("issues", "issue")

        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO issues_issue"
                " (subject, description, project_id, status_id, priority_id, type_id,"
                "  severity_id, owner_id, assigned_to_id, milestone_id, ref,"
                "  created_date, modified_date, version)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 1)"
                " RETURNING id",
                (
                    issue.subject,
                    issue.description,
                    project_id,
                    status_id,
                    priority_id,
                    type_id,
                    severity_id,
                    owner_id,
                    assigned_to_id,
                    milestone_id,
                    now,
                    now,
                ),
            )
            object_id = cur.fetchone()[0]

        ref = RefAllocator(self._conn).allocate(project_id, object_id, content_type_id)

        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE issues_issue SET ref = %s WHERE id = %s",
                (ref, object_id),
            )

        return ref
