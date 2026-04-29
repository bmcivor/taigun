import logging
import pytest
from unittest.mock import MagicMock

from taigun.exceptions import ResolveError
from taigun.resolver import Resolver


def make_resolver(fetchone_return=None):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = fetchone_return
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return Resolver(mock_conn), mock_cursor


class TestResolveProject:
    def test_returns_project_id(self):
        """Setup: project exists in DB.
        Expectations: returns the project ID.
        """
        resolver, _ = make_resolver(fetchone_return=(7,))

        assert resolver.resolve_project("my-project") == 7

    def test_not_found_raises(self):
        """Setup: no project with that slug.
        Expectations: ResolveError naming the slug.
        """
        resolver, _ = make_resolver(fetchone_return=None)
        with pytest.raises(ResolveError, match="my-project"):
            resolver.resolve_project("my-project")


class TestResolveUser:
    def test_returns_user_id(self):
        """Setup: user exists in DB.
        Expectations: returns the user ID.
        """
        resolver, _ = make_resolver(fetchone_return=(3,))

        assert resolver.resolve_user("blake") == 3

    def test_not_found_raises(self):
        """Setup: no user with that username.
        Expectations: ResolveError naming the username.
        """
        resolver, _ = make_resolver(fetchone_return=None)
        with pytest.raises(ResolveError, match="blake"):
            resolver.resolve_user("blake")


class TestResolveStatus:
    def test_returns_status_id(self):
        """Setup: status exists for project and ticket type.
        Expectations: returns the status ID.
        """
        resolver, _ = make_resolver(fetchone_return=(5,))

        assert resolver.resolve_status(1, "In Progress", "story") == 5

    def test_not_found_raises(self):
        """Setup: no matching status.
        Expectations: ResolveError naming the status.
        """
        resolver, _ = make_resolver(fetchone_return=None)
        with pytest.raises(ResolveError, match="In Progress"):
            resolver.resolve_status(1, "In Progress", "story")

    def test_invalid_ticket_type_raises(self):
        """Setup: unrecognised ticket type passed.
        Expectations: ResolveError naming the type.
        """
        resolver, _ = make_resolver()
        with pytest.raises(ResolveError, match="banana"):
            resolver.resolve_status(1, "New", "banana")

    def test_queries_correct_table_for_each_type(self):
        """Setup: each valid ticket type.
        Expectations: query references the correct status table.
        """
        expected = {
            "story": "projects_userstorystatus",
            "task": "projects_taskstatus",
            "issue": "projects_issuestatus",
            "epic": "projects_epicstatus",
        }
        for ticket_type, table in expected.items():
            resolver, cursor = make_resolver(fetchone_return=(1,))
            resolver.resolve_status(1, "New", ticket_type)
            sql = cursor.execute.call_args[0][0]

            assert table in sql


class TestResolvePriority:
    def test_returns_priority_id_on_match(self):
        """Setup: priority exists by name.
        Expectations: returns the priority ID without falling back.
        """
        resolver, _ = make_resolver(fetchone_return=(2,))

        assert resolver.resolve_priority(1, "High") == 2

    def test_falls_back_to_default_on_no_match(self):
        """Setup: no priority by name; project has a default.
        Expectations: returns the default priority ID.
        """
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [None, (9,)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        resolver = Resolver(mock_conn)

        assert resolver.resolve_priority(1, "Unknown") == 9

    def test_no_match_and_no_default_raises(self):
        """Setup: no priority by name and project has no default.
        Expectations: ResolveError raised.
        """
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [None, None]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        resolver = Resolver(mock_conn)
        with pytest.raises(ResolveError, match="default priority"):
            resolver.resolve_priority(1, "Unknown")

    def test_fallback_logs_warning(self, caplog):
        """Setup: priority name not found.
        Expectations: warning logged naming the priority.
        """
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [None, (9,)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        resolver = Resolver(mock_conn)
        with caplog.at_level(logging.WARNING):
            resolver.resolve_priority(1, "Unknown")

        assert "Unknown" in caplog.text


class TestResolveIssueType:
    def test_returns_issue_type_id(self):
        """Setup: issue type exists.
        Expectations: returns the issue type ID.
        """
        resolver, _ = make_resolver(fetchone_return=(4,))

        assert resolver.resolve_issue_type(1, "Bug") == 4

    def test_not_found_raises(self):
        """Setup: no matching issue type.
        Expectations: ResolveError naming the type.
        """
        resolver, _ = make_resolver(fetchone_return=None)
        with pytest.raises(ResolveError, match="Bug"):
            resolver.resolve_issue_type(1, "Bug")


class TestResolveSeverity:
    def test_returns_severity_id(self):
        """Setup: severity exists.
        Expectations: returns the severity ID.
        """
        resolver, _ = make_resolver(fetchone_return=(6,))

        assert resolver.resolve_severity(1, "High") == 6

    def test_not_found_raises(self):
        """Setup: no matching severity.
        Expectations: ResolveError naming the severity.
        """
        resolver, _ = make_resolver(fetchone_return=None)
        with pytest.raises(ResolveError, match="High"):
            resolver.resolve_severity(1, "High")


class TestResolveEpic:
    def test_returns_epic_id(self):
        """Setup: epic exists with that ref.
        Expectations: returns the epic ID.
        """
        resolver, _ = make_resolver(fetchone_return=(11,))

        assert resolver.resolve_epic(1, 42) == 11

    def test_not_found_raises(self):
        """Setup: no epic with that ref.
        Expectations: ResolveError naming the ref.
        """
        resolver, _ = make_resolver(fetchone_return=None)
        with pytest.raises(ResolveError, match="#42"):
            resolver.resolve_epic(1, 42)


class TestResolveContentType:
    def test_returns_content_type_id(self):
        """Setup: content type exists.
        Expectations: returns the content type ID.
        """
        resolver, _ = make_resolver(fetchone_return=(8,))

        assert resolver.resolve_content_type("epics", "epic") == 8

    def test_not_found_raises(self):
        """Setup: content type not found.
        Expectations: ResolveError naming app_label and model.
        """
        resolver, _ = make_resolver(fetchone_return=None)
        with pytest.raises(ResolveError, match="epics.epic"):
            resolver.resolve_content_type("epics", "epic")

    def test_result_is_cached(self):
        """Setup: content type looked up twice with same args.
        Expectations: DB queried only once.
        """
        resolver, cursor = make_resolver(fetchone_return=(8,))
        resolver.resolve_content_type("epics", "epic")
        resolver.resolve_content_type("epics", "epic")

        assert cursor.execute.call_count == 1

    def test_different_keys_each_queried(self):
        """Setup: two different content types looked up.
        Expectations: DB queried once per unique key.
        """
        resolver, cursor = make_resolver(fetchone_return=(8,))
        resolver.resolve_content_type("epics", "epic")
        resolver.resolve_content_type("userstories", "userstory")

        assert cursor.execute.call_count == 2
