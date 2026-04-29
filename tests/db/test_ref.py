import psycopg2.errors
import pytest

from unittest.mock import MagicMock

from taigun.db import RefAllocator


def make_conn(nextval=42):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (nextval,)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    return mock_conn, mock_cursor


class TestRefAllocator:
    def test_returns_ref(self):
        """Setup: sequence exists and returns a value.
        Expectations: allocate returns the ref number.
        """
        mock_conn, _ = make_conn(nextval=7)

        assert RefAllocator(mock_conn).allocate(1, 99, 5) == 7

    def test_calls_correct_sequence(self):
        """Setup: project ID 3.
        Expectations: nextval called on references_project3.
        """
        mock_conn, mock_cursor = make_conn()
        RefAllocator(mock_conn).allocate(3, 99, 5)
        first_call_sql = mock_cursor.execute.call_args_list[0][0][0]

        assert first_call_sql == "SELECT nextval('references_project3')"

    def test_inserts_reference_row(self):
        """Setup: sequence call succeeds.
        Expectations: INSERT into references_reference with correct values.
        """
        mock_conn, mock_cursor = make_conn(nextval=42)
        RefAllocator(mock_conn).allocate(1, 99, 5)
        insert_call = mock_cursor.execute.call_args_list[1]
        sql, params = insert_call[0]

        assert sql == (
            "INSERT INTO references_reference (ref, object_id, content_type_id, project_id)"
            " VALUES (%s, %s, %s, %s)"
        )
        assert params == (42, 99, 5, 1)

    def test_missing_sequence_raises_system_exit(self):
        """Setup: sequence does not exist for the project.
        Expectations: SystemExit with a clear message naming the project.
        """
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.errors.UndefinedTable("no sequence")
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with pytest.raises(SystemExit, match="project 1"):
            RefAllocator(mock_conn).allocate(1, 99, 5)
