from unittest.mock import MagicMock, patch

import pytest

from taigun.db.task import TaskWriter
from taigun.models import Task

from .conftest import FIXED_NOW, FIXED_ORDER


def make_resolver():
    mock_resolver = MagicMock()
    mock_resolver.resolve_project.return_value = 1
    mock_resolver.resolve_user.return_value = 5
    mock_resolver.resolve_default_status.return_value = 2
    mock_resolver.resolve_status.return_value = 2
    mock_resolver.resolve_story.return_value = 20
    mock_resolver.resolve_milestone.return_value = 4
    mock_resolver.resolve_content_type.return_value = 8

    return mock_resolver


def make_task(**kwargs):
    defaults = {"project": "my-project", "subject": "Do the subthing"}
    return Task(**{**defaults, **kwargs})


class TestTaskWriter:
    def test_returns_ref(self, mock_conn):
        """Setup: all resolvers succeed; RefAllocator returns 42.
        Expectations: write returns the allocated ref.
        """
        writer = TaskWriter(mock_conn, make_resolver())
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            ref = writer.write(make_task(), "admin")

        assert ref == 42

    def test_insert_sql_and_params(self, mock_conn, mock_cursor):
        """Setup: task with no optional fields.
        Expectations: INSERT SQL and params are exact.
        """
        writer = TaskWriter(mock_conn, make_resolver())
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(description="desc"), "admin")

        sql, params = mock_cursor.execute.call_args_list[0][0]

        assert sql == (
            "INSERT INTO tasks_task"
            " (subject, description, project_id, status_id, owner_id,"
            "  user_story_id, assigned_to_id, milestone_id, ref,"
            "  created_date, modified_date, version, us_order, taskboard_order)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 1, %s, %s)"
            " RETURNING id"
        )
        assert params == (
            "Do the subthing",
            "desc",
            1,
            2,
            5,
            None,
            None,
            None,
            FIXED_NOW,
            FIXED_NOW,
            FIXED_ORDER,
            FIXED_ORDER,
        )

    def test_update_sets_ref(self, mock_conn, mock_cursor):
        """Setup: INSERT returns object_id 101; RefAllocator returns ref 42.
        Expectations: UPDATE SQL sets ref = 42 on row 101.
        """
        writer = TaskWriter(mock_conn, make_resolver())
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(), "admin")

        sql, params = mock_cursor.execute.call_args_list[3][0]

        assert sql == "UPDATE tasks_task SET ref = %s WHERE id = %s"
        assert params == (42, 101)

    def test_resolves_project(self, mock_conn):
        """Setup: task with project slug.
        Expectations: resolve_project called with the slug.
        """
        mock_resolver = make_resolver()
        writer = TaskWriter(mock_conn, mock_resolver)
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(project="my-project"), "admin")

        mock_resolver.resolve_project.assert_called_once_with("my-project")

    def test_resolves_parent_when_set(self, mock_conn):
        """Setup: task with parent ref set.
        Expectations: resolve_story called with project_id and ref.
        """
        mock_resolver = make_resolver()
        writer = TaskWriter(mock_conn, mock_resolver)
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(parent=5), "admin")

        mock_resolver.resolve_story.assert_called_once_with(1, 5)

    def test_user_story_id_in_insert_when_parent_set(self, mock_conn, mock_cursor):
        """Setup: task with parent ref set; resolve_story returns 20.
        Expectations: user_story_id in INSERT params is 20.
        """
        writer = TaskWriter(mock_conn, make_resolver())
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(parent=5), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert params[5] == 20

    def test_user_story_id_none_when_no_parent(self, mock_conn, mock_cursor):
        """Setup: task with no parent.
        Expectations: user_story_id in INSERT params is None.
        """
        writer = TaskWriter(mock_conn, make_resolver())
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert params[5] is None

    def test_skips_resolve_story_when_no_parent(self, mock_conn):
        """Setup: task with no parent.
        Expectations: resolve_story not called.
        """
        mock_resolver = make_resolver()
        writer = TaskWriter(mock_conn, mock_resolver)
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(), "admin")

        mock_resolver.resolve_story.assert_not_called()

    def test_resolves_milestone_when_set(self, mock_conn):
        """Setup: task with milestone set.
        Expectations: resolve_milestone called with project_id and milestone name.
        """
        mock_resolver = make_resolver()
        writer = TaskWriter(mock_conn, mock_resolver)
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(milestone="Sprint 1"), "admin")

        mock_resolver.resolve_milestone.assert_called_once_with(1, "Sprint 1")

    def test_assigned_to_id_in_insert_when_assignee_set(self, mock_conn, mock_cursor):
        """Setup: task with assignee; resolve_user returns 5 for owner and 8 for assignee.
        Expectations: assigned_to_id in INSERT params is 8.
        """
        mock_resolver = make_resolver()
        mock_resolver.resolve_user.side_effect = [5, 8]
        writer = TaskWriter(mock_conn, mock_resolver)
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(assignee="alice"), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert params[6] == 8

    def test_assigned_to_id_none_when_no_assignee(self, mock_conn, mock_cursor):
        """Setup: task with no assignee.
        Expectations: assigned_to_id in INSERT params is None.
        """
        writer = TaskWriter(mock_conn, make_resolver())
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert params[6] is None

    def test_execute_count_no_optionals(self, mock_conn, mock_cursor):
        """Setup: task with no optional fields.
        Expectations: exactly 4 execute calls (INSERT, nextval, INSERT ref, UPDATE).
        """
        writer = TaskWriter(mock_conn, make_resolver())
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_task(), "admin")

        assert mock_cursor.execute.call_count == 4
