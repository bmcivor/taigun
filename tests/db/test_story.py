from unittest.mock import MagicMock, patch

import pytest

from taigun.db.story import StoryWriter
from taigun.models import Story

from .conftest import FIXED_NOW, FIXED_ORDER


def make_resolver():
    mock_resolver = MagicMock()
    mock_resolver.resolve_project.return_value = 1
    mock_resolver.resolve_user.return_value = 5
    mock_resolver.resolve_default_status.return_value = 2
    mock_resolver.resolve_status.return_value = 2
    mock_resolver.resolve_priority.return_value = 3
    mock_resolver.resolve_content_type.return_value = 7
    mock_resolver.resolve_epic.return_value = 11
    mock_resolver.resolve_milestone.return_value = 4
    return mock_resolver


def make_story(**kwargs):
    defaults = {"project": "my-project", "subject": "Do the thing"}
    return Story(**{**defaults, **kwargs})


class TestStoryWriter:
    @pytest.fixture
    def resolver(self):
        return make_resolver()

    @pytest.fixture
    def writer(self, mock_conn, resolver):
        return StoryWriter(mock_conn, resolver)

    def test_returns_ref(self, writer):
        """Setup: all resolvers succeed; RefAllocator returns 42.
        Expectations: write returns the allocated ref.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            ref = writer.write(make_story(), "admin")

        assert ref == 42

    def test_insert_sql_and_params(self, writer, mock_cursor):
        """Setup: story with no optional fields.
        Expectations: INSERT SQL and params are exact.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_story(description="desc"), "admin")

        sql, params = mock_cursor.execute.call_args_list[0][0]

        assert sql == (
            "INSERT INTO userstories_userstory"
            " (subject, description, project_id, status_id, priority_id, owner_id,"
            "  assigned_to_id, milestone_id, ref, created_date, modified_date, version,"
            "  backlog_order, sprint_order, kanban_order)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 1, %s, %s, %s)"
            " RETURNING id"
        )
        assert params == (
            "Do the thing",
            "desc",
            1,
            2,
            3,
            5,
            None,
            None,
            FIXED_NOW,
            FIXED_NOW,
            FIXED_ORDER,
            FIXED_ORDER,
            FIXED_ORDER,
        )

    def test_update_sets_ref(self, writer, mock_cursor):
        """Setup: INSERT returns object_id 101; RefAllocator returns ref 42.
        Expectations: UPDATE SQL sets ref = 42 on row 101.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_story(), "admin")

        sql, params = mock_cursor.execute.call_args_list[3][0]

        assert sql == "UPDATE userstories_userstory SET ref = %s WHERE id = %s"
        assert params == (42, 101)

    def test_resolves_project(self, writer, resolver):
        """Setup: story with project slug.
        Expectations: resolve_project called with the slug.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_story(project="my-project"), "admin")

        resolver.resolve_project.assert_called_once_with("my-project")

    def test_resolves_milestone_when_set(self, writer, resolver):
        """Setup: story with milestone set.
        Expectations: resolve_milestone called with project_id and milestone name.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_story(milestone="Sprint 1"), "admin")

        resolver.resolve_milestone.assert_called_once_with(1, "Sprint 1")

    def test_inserts_assigned_users_when_assignee_set(self, writer, resolver, mock_cursor):
        """Setup: story with assignee set; resolve_user returns 5 for owner and 8 for assignee.
        Expectations: M2M INSERT SQL and params are exact.
        """
        resolver.resolve_user.side_effect = [5, 8]
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_story(assignee="alice"), "admin")

        sql, params = mock_cursor.execute.call_args_list[4][0]

        assert sql == (
            "INSERT INTO userstories_userstory_assigned_users"
            " (userstory_id, user_id)"
            " VALUES (%s, %s)"
        )
        assert params == (101, 8)

    def test_skips_assigned_users_when_no_assignee(self, writer, mock_cursor):
        """Setup: story with no assignee.
        Expectations: exactly 4 execute calls (INSERT, nextval, INSERT ref, UPDATE).
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_story(), "admin")

        assert mock_cursor.execute.call_count == 4

    def test_inserts_epic_relation_when_epic_set(self, writer, mock_cursor):
        """Setup: story with epic ref set; resolve_epic returns 11.
        Expectations: epics_relateduserstory INSERT SQL and params are exact.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_story(epic=5), "admin")

        sql, params = mock_cursor.execute.call_args_list[4][0]

        assert sql == (
            "INSERT INTO epics_relateduserstory (epic_id, user_story_id)"
            " VALUES (%s, %s)"
        )
        assert params == (11, 101)

    def test_skips_epic_relation_when_no_epic(self, writer, mock_cursor):
        """Setup: story with no epic.
        Expectations: exactly 4 execute calls (INSERT, nextval, INSERT ref, UPDATE).
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_story(), "admin")

        assert mock_cursor.execute.call_count == 4
