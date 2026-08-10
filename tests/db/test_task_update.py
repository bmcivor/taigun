import datetime

import psycopg2.extensions
from factories import make_project

from taigun.db.story import StoryWriter
from taigun.db.task import TaskWriter
from taigun.models import Story, Task
from taigun.resolver import Resolver


class TestTaskUpdate:
    def test_updates_subject_and_description(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: project + parent story + task with original values.
        Expectations: update rewrites subject/description; DB reflects.
        """
        make_project(real_conn)
        parent_ref = StoryWriter(real_conn, Resolver(real_conn)).write(
            Story(project="test-project", subject="Parent"), "admin"
        )
        ref = TaskWriter(real_conn, Resolver(real_conn)).write(
            Task(project="test-project", subject="Original", parent=parent_ref),
            "admin",
        )

        TaskWriter(real_conn, Resolver(real_conn)).update(
            Task(
                project="test-project",
                subject="Updated",
                description="Body text",
                parent=parent_ref,
            ),
            ref=ref,
            metadata_keys={"type", "project", "parent"},
            acting_user="admin",
            last_pushed_at=_now_iso(),
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT subject, description FROM tasks_task WHERE ref = %s",
                (ref,),
            )
            row = cur.fetchone()

        assert row == ("Updated", "Body text")


def _now_iso() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )
