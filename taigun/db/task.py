from typing import Optional

from taigun.db.base import BaseWriter
from taigun.models import Task


class TaskWriter(BaseWriter):
    """Inserts a Task and all related rows into the Taiga database.

    Must be used within a transaction managed by ConnectionManager.
    """

    _ticket_type = "task"
    _content_type = ("tasks", "task")
    _table = "tasks_task"

    def write(self, task: Task, acting_user: str) -> int:
        """Insert a task and return the allocated ref number.

        Resolves all FK references, inserts into tasks_task,
        and allocates a project-scoped ref.

        Args:
            task: Populated Task model.
            acting_user: Username of the acting user (becomes owner_id).

        Returns:
            Allocated ref number.
        """
        project_id, owner_id, status_id, now = self._resolve_common(task, acting_user)
        order = int(now.timestamp())

        user_story_id: Optional[int] = None
        if task.parent is not None:
            user_story_id = self._resolver.resolve_story(project_id, task.parent)

        assigned_to_id: Optional[int] = None
        if task.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(task.assignee)

        milestone_id: Optional[int] = None
        if task.milestone is not None:
            milestone_id = self._resolver.resolve_milestone(project_id, task.milestone)

        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks_task"
                " (subject, description, project_id, status_id, owner_id,"
                "  user_story_id, assigned_to_id, milestone_id, ref,"
                "  created_date, modified_date, version, us_order, taskboard_order)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 1, %s, %s)"
                " RETURNING id",
                (
                    task.subject,
                    task.description,
                    project_id,
                    status_id,
                    owner_id,
                    user_story_id,
                    assigned_to_id,
                    milestone_id,
                    now,
                    now,
                    order,
                    order,
                ),
            )
            object_id = cur.fetchone()[0]

        return self._allocate_and_set_ref(project_id, object_id)
