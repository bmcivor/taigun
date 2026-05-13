import pytest

from taigun.db.epic import EpicWriter
from taigun.db.lister import Lister
from taigun.models import Epic
from taigun.resolver import Resolver

from factories import make_project


@pytest.mark.xfail(reason="ticket 023: writer SQL bugs not yet fixed")
class TestEpicWriter:
    def test_returns_positive_ref(self, real_conn):
        """Setup: project exists; epic has only required fields.
        Expectations: writer.write returns a positive ref number.
        """
        make_project(real_conn)
        writer = EpicWriter(real_conn, Resolver(real_conn))

        ref = writer.write(Epic(project="test-project", subject="Big feature"), "admin")

        assert ref > 0

    def test_lister_finds_written_epic_with_subject(self, real_conn):
        """Setup: project exists; epic written with subject 'Big feature'.
        Expectations: Lister.list_epics for that project contains (ref, 'Big feature').
        """
        project_id = make_project(real_conn)
        writer = EpicWriter(real_conn, Resolver(real_conn))

        ref = writer.write(Epic(project="test-project", subject="Big feature"), "admin")

        epics = Lister(real_conn).list_epics(project_id)

        assert (ref, "Big feature") in epics

    def test_ref_is_sequential_within_project(self, real_conn):
        """Setup: project exists; two epics written in succession.
        Expectations: second ref is exactly one greater than the first.
        """
        make_project(real_conn)
        writer = EpicWriter(real_conn, Resolver(real_conn))

        ref_a = writer.write(Epic(project="test-project", subject="A"), "admin")
        ref_b = writer.write(Epic(project="test-project", subject="B"), "admin")

        assert ref_b == ref_a + 1

    def test_with_assignee_succeeds(self, real_conn):
        """Setup: epic with assignee set to the existing admin user.
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = EpicWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Epic(project="test-project", subject="Assigned", assignee="admin"),
            "admin",
        )

        assert ref > 0

    def test_with_explicit_color_succeeds(self, real_conn):
        """Setup: epic with explicit color #abcdef.
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = EpicWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Epic(project="test-project", subject="Coloured", color="#abcdef"),
            "admin",
        )

        assert ref > 0

    def test_with_auto_color_succeeds(self, real_conn):
        """Setup: epic with no color (writer picks a random one).
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = EpicWriter(real_conn, Resolver(real_conn))

        ref = writer.write(Epic(project="test-project", subject="No colour"), "admin")

        assert ref > 0

    def test_with_custom_status(self, real_conn):
        """Setup: epic with status set to a known kanban epic status.
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = EpicWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Epic(project="test-project", subject="WIP", status="In progress"),
            "admin",
        )

        assert ref > 0
