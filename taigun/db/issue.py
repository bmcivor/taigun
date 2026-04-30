from typing import Optional

from taigun.db.base import BaseWriter
from taigun.models import Issue


class IssueWriter(BaseWriter):
    """Inserts an Issue and all related rows into the Taiga database.

    Must be used within a transaction managed by ConnectionManager.
    """

    _ticket_type = "issue"
    _content_type = ("issues", "issue")
    _table = "issues_issue"

    def write(self, issue: Issue, acting_user: str) -> int:
        """Insert an issue and return the allocated ref number.

        Resolves all FK references, inserts into issues_issue,
        and allocates a project-scoped ref.

        Args:
            issue: Populated Issue model.
            acting_user: Username of the acting user (becomes owner_id).

        Returns:
            Allocated ref number.
        """
        project_id, owner_id, status_id, now = self._resolve_common(issue, acting_user)
        priority_id = self._resolver.resolve_priority(project_id, issue.priority)
        type_id = self._resolver.resolve_issue_type(project_id, issue.issue_type)
        severity_id = self._resolver.resolve_severity(project_id, issue.severity)

        assigned_to_id: Optional[int] = None
        if issue.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(issue.assignee)

        milestone_id: Optional[int] = None
        if issue.milestone is not None:
            milestone_id = self._resolver.resolve_milestone(project_id, issue.milestone)

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

        return self._allocate_and_set_ref(project_id, object_id)
