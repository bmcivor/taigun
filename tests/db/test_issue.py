import datetime
from unittest.mock import MagicMock, patch

from taigun.db.issue import IssueWriter
from taigun.models import Issue


FIXED_NOW = datetime.datetime(2024, 1, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)


def make_writer():
    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = [(101,), (42,)]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_resolver = MagicMock()
    mock_resolver.resolve_project.return_value = 1
    mock_resolver.resolve_user.return_value = 5
    mock_resolver.resolve_default_status.return_value = 2
    mock_resolver.resolve_status.return_value = 2
    mock_resolver.resolve_priority.return_value = 3
    mock_resolver.resolve_issue_type.return_value = 6
    mock_resolver.resolve_severity.return_value = 7
    mock_resolver.resolve_content_type.return_value = 9
    mock_resolver.resolve_milestone.return_value = 4

    return IssueWriter(mock_conn, mock_resolver), mock_cursor, mock_resolver


def make_issue(**kwargs):
    defaults = {"project": "my-project", "subject": "Something is broken"}
    return Issue(**{**defaults, **kwargs})


class TestIssueWriter:
    def test_returns_ref(self):
        """Setup: all resolvers succeed; RefAllocator returns 42.
        Expectations: write returns the allocated ref.
        """
        writer, _, _ = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            ref = writer.write(make_issue(), "admin")

        assert ref == 42

    def test_insert_sql_and_params(self):
        """Setup: issue with no optional fields.
        Expectations: INSERT SQL and params are exact.
        """
        writer, mock_cursor, _ = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(description="desc"), "admin")

        sql, params = mock_cursor.execute.call_args_list[0][0]

        assert sql == (
            "INSERT INTO issues_issue"
            " (subject, description, project_id, status_id, priority_id, type_id,"
            "  severity_id, owner_id, assigned_to_id, milestone_id, ref,"
            "  created_date, modified_date, version)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 1)"
            " RETURNING id"
        )
        assert params == (
            "Something is broken",
            "desc",
            1,
            2,
            3,
            6,
            7,
            5,
            None,
            None,
            FIXED_NOW,
            FIXED_NOW,
        )

    def test_update_sets_ref(self):
        """Setup: INSERT returns object_id 101; RefAllocator returns ref 42.
        Expectations: UPDATE SQL sets ref = 42 on row 101.
        """
        writer, mock_cursor, _ = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(), "admin")

        sql, params = mock_cursor.execute.call_args_list[3][0]

        assert sql == "UPDATE issues_issue SET ref = %s WHERE id = %s"
        assert params == (42, 101)

    def test_resolves_project(self):
        """Setup: issue with project slug.
        Expectations: resolve_project called with the slug.
        """
        writer, _, mock_resolver = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(project="my-project"), "admin")

        mock_resolver.resolve_project.assert_called_once_with("my-project")

    def test_resolves_issue_type_when_set(self):
        """Setup: issue with issue_type set.
        Expectations: resolve_issue_type called with project_id and type name.
        """
        writer, _, mock_resolver = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(issue_type="Bug"), "admin")

        mock_resolver.resolve_issue_type.assert_called_once_with(1, "Bug")

    def test_resolves_issue_type_none_passes_none(self):
        """Setup: issue with no issue_type.
        Expectations: resolve_issue_type called with None (resolver handles fallback).
        """
        writer, _, mock_resolver = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(), "admin")

        mock_resolver.resolve_issue_type.assert_called_once_with(1, None)

    def test_resolves_severity_when_set(self):
        """Setup: issue with severity set.
        Expectations: resolve_severity called with project_id and severity name.
        """
        writer, _, mock_resolver = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(severity="Critical"), "admin")

        mock_resolver.resolve_severity.assert_called_once_with(1, "Critical")

    def test_resolves_severity_none_passes_none(self):
        """Setup: issue with no severity.
        Expectations: resolve_severity called with None (resolver handles fallback).
        """
        writer, _, mock_resolver = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(), "admin")

        mock_resolver.resolve_severity.assert_called_once_with(1, None)

    def test_resolves_milestone_when_set(self):
        """Setup: issue with milestone set.
        Expectations: resolve_milestone called with project_id and milestone name.
        """
        writer, _, mock_resolver = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(milestone="Sprint 1"), "admin")

        mock_resolver.resolve_milestone.assert_called_once_with(1, "Sprint 1")

    def test_assigned_to_id_in_insert_when_assignee_set(self):
        """Setup: issue with assignee; resolve_user returns 5 for owner and 8 for assignee.
        Expectations: assigned_to_id in INSERT params is 8.
        """
        writer, mock_cursor, mock_resolver = make_writer()
        mock_resolver.resolve_user.side_effect = [5, 8]
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(assignee="alice"), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert params[8] == 8

    def test_assigned_to_id_none_when_no_assignee(self):
        """Setup: issue with no assignee.
        Expectations: assigned_to_id in INSERT params is None.
        """
        writer, mock_cursor, _ = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert params[8] is None

    def test_execute_count_no_optionals(self):
        """Setup: issue with no optional relational fields.
        Expectations: exactly 4 execute calls (INSERT, nextval, INSERT ref, UPDATE).
        """
        writer, mock_cursor, _ = make_writer()
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_issue(), "admin")

        assert mock_cursor.execute.call_count == 4
