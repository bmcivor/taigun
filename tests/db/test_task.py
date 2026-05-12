import pytest

from taigun.db.task import TaskWriter
from taigun.models import Task
from taigun.resolver import Resolver

from factories import make_project


@pytest.mark.xfail(reason="ticket 023: writer SQL bugs not yet fixed")
class TestTaskWriter:
    def test_returns_positive_ref(self, real_conn):
        """Setup: project exists; task has only required fields.
        Expectations: writer.write returns a positive ref number.
        """
        make_project(real_conn)
        writer = TaskWriter(real_conn, Resolver(real_conn))

        ref = writer.write(Task(project="test-project", subject="Do thing"), "admin")

        assert ref > 0

    def test_ref_is_sequential_within_project(self, real_conn):
        """Setup: project exists; two tasks written in succession.
        Expectations: second ref is exactly one greater than the first.
        """
        make_project(real_conn)
        writer = TaskWriter(real_conn, Resolver(real_conn))

        ref_a = writer.write(Task(project="test-project", subject="A"), "admin")
        ref_b = writer.write(Task(project="test-project", subject="B"), "admin")

        assert ref_b == ref_a + 1

    def test_with_assignee_succeeds(self, real_conn):
        """Setup: task with assignee set to the existing admin user.
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = TaskWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Task(project="test-project", subject="Do thing", assignee="admin"),
            "admin",
        )

        assert ref > 0
