import pytest

from taigun.db.issue import IssueWriter
from taigun.models import Issue
from taigun.resolver import Resolver

from factories import make_milestone, make_project


class TestIssueWriter:
    def test_returns_positive_ref(self, real_conn):
        """Setup: project exists; issue has only required fields.
        Expectations: writer.write returns a positive ref number.
        """
        make_project(real_conn)
        writer = IssueWriter(real_conn, Resolver(real_conn))

        ref = writer.write(Issue(project="test-project", subject="Broken"), "admin")

        assert ref > 0

    def test_ref_is_sequential_within_project(self, real_conn):
        """Setup: project exists; two issues written in succession.
        Expectations: second ref is exactly one greater than the first.
        """
        make_project(real_conn)
        writer = IssueWriter(real_conn, Resolver(real_conn))

        ref_a = writer.write(Issue(project="test-project", subject="A"), "admin")
        ref_b = writer.write(Issue(project="test-project", subject="B"), "admin")

        assert ref_b == ref_a + 1

    def test_with_assignee_succeeds(self, real_conn):
        """Setup: issue with assignee set to the existing admin user.
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = IssueWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Issue(project="test-project", subject="Broken", assignee="admin"),
            "admin",
        )

        assert ref > 0

    def test_with_milestone_succeeds(self, real_conn):
        """Setup: project + one milestone named 'Sprint 1'.
        Expectations: writer.write returns a ref without raising.
        """
        project_id = make_project(real_conn)
        make_milestone(real_conn, project_id, "Sprint 1")
        writer = IssueWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Issue(project="test-project", subject="Broken", milestone="Sprint 1"),
            "admin",
        )

        assert ref > 0

    def test_with_custom_issue_type(self, real_conn):
        """Setup: issue with issue_type set to a known kanban type ("Question").
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = IssueWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Issue(project="test-project", subject="Question", issue_type="Question"),
            "admin",
        )

        assert ref > 0

    def test_with_custom_severity(self, real_conn):
        """Setup: issue with severity set to a known kanban severity ("Critical").
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = IssueWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Issue(project="test-project", subject="Crash", severity="Critical"),
            "admin",
        )

        assert ref > 0

    def test_with_custom_priority(self, real_conn):
        """Setup: issue with priority set to a known kanban priority ("High").
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = IssueWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Issue(project="test-project", subject="Urgent", priority="High"),
            "admin",
        )

        assert ref > 0

    def test_with_custom_status(self, real_conn):
        """Setup: issue with status set to a known kanban issue status.
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = IssueWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Issue(project="test-project", subject="WIP", status="In progress"),
            "admin",
        )

        assert ref > 0
