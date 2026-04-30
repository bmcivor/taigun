import datetime
from typing import Optional

from taigun.db.ref import RefAllocator
from taigun.models import Task


class TaskWriter:
    """Inserts a Task and all related rows into the Taiga database.

    Must be used within a transaction managed by ConnectionManager.
    """

    def __init__(self, conn, resolver) -> None:
        self._conn = conn
        self._resolver = resolver

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
        now = datetime.datetime.now(datetime.timezone.utc)
        order = int(now.timestamp())

        project_id = self._resolver.resolve_project(task.project)
        owner_id = self._resolver.resolve_user(acting_user)

        if task.status is not None:
            status_id = self._resolver.resolve_status(project_id, task.status, "task")
        else:
            status_id = self._resolver.resolve_default_status(project_id, "task")

        user_story_id: Optional[int] = None
        if task.parent is not None:
            user_story_id = self._resolver.resolve_story(project_id, task.parent)

        assigned_to_id: Optional[int] = None
        if task.assignee is not None:
            assigned_to_id = self._resolver.resolve_user(task.assignee)

        milestone_id: Optional[int] = None
        if task.milestone is not None:
            milestone_id = self._resolver.resolve_milestone(project_id, task.milestone)

        content_type_id = self._resolver.resolve_content_type("tasks", "task")

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

        ref = RefAllocator(self._conn).allocate(project_id, object_id, content_type_id)

        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks_task SET ref = %s WHERE id = %s",
                (ref, object_id),
            )

        return ref
