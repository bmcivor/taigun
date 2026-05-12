import pytest

from taigun.db.issue import IssueWriter
from taigun.models import Issue
from taigun.resolver import Resolver

from factories import make_project


@pytest.mark.xfail(reason="ticket 023: writer SQL bugs not yet fixed")
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
