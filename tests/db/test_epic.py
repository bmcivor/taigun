import re
from unittest.mock import MagicMock, patch

import pytest

from taigun.db.epic import EpicWriter
from taigun.models import Epic

from .conftest import FIXED_NOW, FIXED_ORDER


def make_resolver():
    mock_resolver = MagicMock()
    mock_resolver.resolve_project.return_value = 1
    mock_resolver.resolve_user.return_value = 5
    mock_resolver.resolve_default_status.return_value = 2
    mock_resolver.resolve_status.return_value = 2
    mock_resolver.resolve_content_type.return_value = 10
    return mock_resolver


def make_epic(**kwargs):
    defaults = {"project": "my-project", "subject": "Big feature"}
    return Epic(**{**defaults, **kwargs})


class TestEpicWriter:
    @pytest.fixture
    def resolver(self):
        return make_resolver()

    @pytest.fixture
    def writer(self, mock_conn, resolver):
        return EpicWriter(mock_conn, resolver)

    def test_returns_ref(self, writer):
        """Setup: all resolvers succeed; RefAllocator returns 42.
        Expectations: write returns the allocated ref.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            ref = writer.write(make_epic(), "admin")

        assert ref == 42

    def test_insert_sql_and_params(self, writer, mock_cursor):
        """Setup: epic with color set, no optional fields.
        Expectations: INSERT SQL and params are exact.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_epic(description="desc", color="#abcdef"), "admin")

        sql, params = mock_cursor.execute.call_args_list[0][0]

        assert sql == (
            "INSERT INTO epics_epic"
            " (subject, description, project_id, status_id, owner_id,"
            "  color, assigned_to_id, ref, created_date, modified_date, version, epics_order)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 1, %s)"
            " RETURNING id"
        )
        assert params == (
            "Big feature",
            "desc",
            1,
            2,
            5,
            "#abcdef",
            None,
            FIXED_NOW,
            FIXED_NOW,
            FIXED_ORDER,
        )

    def test_update_sets_ref(self, writer, mock_cursor):
        """Setup: INSERT returns object_id 101; RefAllocator returns ref 42.
        Expectations: UPDATE SQL sets ref = 42 on row 101.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_epic(color="#abcdef"), "admin")

        sql, params = mock_cursor.execute.call_args_list[3][0]

        assert sql == "UPDATE epics_epic SET ref = %s WHERE id = %s"
        assert params == (42, 101)

    def test_resolves_project(self, writer, resolver):
        """Setup: epic with project slug.
        Expectations: resolve_project called with the slug.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_epic(color="#abcdef", project="my-project"), "admin")

        resolver.resolve_project.assert_called_once_with("my-project")

    def test_uses_color_when_set(self, writer, mock_cursor):
        """Setup: epic with color set to #aabbcc.
        Expectations: color in INSERT params is #aabbcc.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_epic(color="#aabbcc"), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert params[5] == "#aabbcc"

    def test_generates_random_color_when_not_set(self, writer, mock_cursor):
        """Setup: epic with no color.
        Expectations: color in INSERT params is a valid #rrggbb hex string.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_epic(), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert re.fullmatch(r"#[0-9a-f]{6}", params[5])

    def test_random_color_uses_random_module(self, writer, mock_cursor):
        """Setup: epic with no color; random.randint patched to return fixed value.
        Expectations: color in INSERT params is derived from the patched value.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            with patch("taigun.db.epic.random.randint", return_value=0x123456):
                writer.write(make_epic(), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert params[5] == "#123456"

    def test_assigned_to_id_in_insert_when_assignee_set(self, writer, resolver, mock_cursor):
        """Setup: epic with assignee; resolve_user returns 5 for owner and 8 for assignee.
        Expectations: assigned_to_id in INSERT params is 8.
        """
        resolver.resolve_user.side_effect = [5, 8]
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_epic(color="#abcdef", assignee="alice"), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert params[6] == 8

    def test_assigned_to_id_none_when_no_assignee(self, writer, mock_cursor):
        """Setup: epic with no assignee.
        Expectations: assigned_to_id in INSERT params is None.
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_epic(color="#abcdef"), "admin")

        _, params = mock_cursor.execute.call_args_list[0][0]
        assert params[6] is None

    def test_execute_count_no_optionals(self, writer, mock_cursor):
        """Setup: epic with no optional fields.
        Expectations: exactly 4 execute calls (INSERT, nextval, INSERT ref, UPDATE).
        """
        with patch("taigun.db.base.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_NOW
            writer.write(make_epic(color="#abcdef"), "admin")

        assert mock_cursor.execute.call_count == 4
