import psycopg2
import pytest

from unittest.mock import MagicMock, patch

from taigun.config import Profile
from taigun.db import ConnectionManager


PROFILE = Profile(
    host="localhost",
    port=5432,
    database="taiga",
    username="taiga",
    password="secret",
    acting_user="admin",
)


class TestConnectionManager:
    def test_connect_yields_connection(self):
        """Setup: valid profile, psycopg2.connect succeeds.
        Expectations: context manager yields the connection object.
        """
        mock_conn = MagicMock()
        with patch("taigun.db.connection.psycopg2.connect", return_value=mock_conn):
            manager = ConnectionManager(PROFILE)
            with manager.connect() as conn:
                assert conn is mock_conn

    def test_commits_on_clean_exit(self):
        """Setup: context block completes without exception.
        Expectations: commit is called on the connection.
        """
        mock_conn = MagicMock()
        with patch("taigun.db.connection.psycopg2.connect", return_value=mock_conn):
            with ConnectionManager(PROFILE).connect():
                pass

        mock_conn.commit.assert_called_once()

    def test_rolls_back_on_exception(self):
        """Setup: exception raised inside context block.
        Expectations: rollback is called and exception is re-raised.
        """
        mock_conn = MagicMock()
        with patch("taigun.db.connection.psycopg2.connect", return_value=mock_conn):
            with pytest.raises(RuntimeError):
                with ConnectionManager(PROFILE).connect():
                    raise RuntimeError("something went wrong")

        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    def test_closes_connection_on_clean_exit(self):
        """Setup: context block completes without exception.
        Expectations: connection is closed.
        """
        mock_conn = MagicMock()
        with patch("taigun.db.connection.psycopg2.connect", return_value=mock_conn):
            with ConnectionManager(PROFILE).connect():
                pass

        mock_conn.close.assert_called_once()

    def test_closes_connection_on_exception(self):
        """Setup: exception raised inside context block.
        Expectations: connection is still closed.
        """
        mock_conn = MagicMock()
        with patch("taigun.db.connection.psycopg2.connect", return_value=mock_conn):
            with pytest.raises(RuntimeError):
                with ConnectionManager(PROFILE).connect():
                    raise RuntimeError("something went wrong")

        mock_conn.close.assert_called_once()

    def test_connection_error_raises_system_exit(self):
        """Setup: psycopg2.connect raises OperationalError.
        Expectations: SystemExit raised with a clear message.
        """
        with patch("taigun.db.connection.psycopg2.connect", side_effect=psycopg2.OperationalError("timeout")):
            with pytest.raises(SystemExit, match="Could not connect"):
                with ConnectionManager(PROFILE).connect():
                    pass

    def test_connect_passes_correct_credentials(self):
        """Setup: profile with known credentials.
        Expectations: psycopg2.connect called with matching arguments.
        """
        mock_conn = MagicMock()
        with patch("taigun.db.connection.psycopg2.connect", return_value=mock_conn) as mock_connect:
            with ConnectionManager(PROFILE).connect():
                pass

        mock_connect.assert_called_once_with(
            host="localhost",
            port=5432,
            dbname="taiga",
            user="taiga",
            password="secret",
        )
