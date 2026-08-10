from unittest.mock import MagicMock

import psycopg2
import pytest

from taigun.config import Profile
from taigun.db import ConnectionManager
from taigun.exceptions import DatabaseConnectionError

PROFILE = Profile(
    host="localhost",
    port=5432,
    database="taiga",
    username="taiga",
    password="secret",
    acting_user="admin",
)


def _factory_returning(mock_conn) -> MagicMock:
    """Return a MagicMock configured to hand out ``mock_conn`` on call."""
    factory = MagicMock(return_value=mock_conn)
    return factory


class TestConnectionManager:
    def test_connect_yields_connection(self):
        """Setup: valid profile, factory returns a mock connection.
        Expectations: context manager yields the connection object.
        """
        mock_conn = MagicMock()
        manager = ConnectionManager(
            PROFILE, _connection_factory=_factory_returning(mock_conn)
        )

        with manager.connect() as conn:
            assert conn is mock_conn

    def test_commits_on_clean_exit(self):
        """Setup: context block completes without exception.
        Expectations: commit is called on the connection.
        """
        mock_conn = MagicMock()
        manager = ConnectionManager(
            PROFILE, _connection_factory=_factory_returning(mock_conn)
        )

        with manager.connect():
            pass

        mock_conn.commit.assert_called_once()

    def test_rolls_back_on_exception(self):
        """Setup: exception raised inside context block.
        Expectations: rollback is called and exception is re-raised.
        """
        mock_conn = MagicMock()
        manager = ConnectionManager(
            PROFILE, _connection_factory=_factory_returning(mock_conn)
        )

        with pytest.raises(RuntimeError):
            with manager.connect():
                raise RuntimeError("something went wrong")

        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    def test_closes_connection_on_clean_exit(self):
        """Setup: context block completes without exception.
        Expectations: connection is closed.
        """
        mock_conn = MagicMock()
        manager = ConnectionManager(
            PROFILE, _connection_factory=_factory_returning(mock_conn)
        )

        with manager.connect():
            pass

        mock_conn.close.assert_called_once()

    def test_closes_connection_on_exception(self):
        """Setup: exception raised inside context block.
        Expectations: connection is still closed.
        """
        mock_conn = MagicMock()
        manager = ConnectionManager(
            PROFILE, _connection_factory=_factory_returning(mock_conn)
        )

        with pytest.raises(RuntimeError):
            with manager.connect():
                raise RuntimeError("something went wrong")

        mock_conn.close.assert_called_once()

    def test_connection_error_raises_database_connection_error(self):
        """Setup: factory raises OperationalError.
        Expectations: DatabaseConnectionError raised with a clear message.
        """
        factory = MagicMock(side_effect=psycopg2.OperationalError("timeout"))
        manager = ConnectionManager(PROFILE, _connection_factory=factory)

        with pytest.raises(DatabaseConnectionError, match="Could not connect"):
            with manager.connect():
                pass

    def test_dry_run_rolls_back_on_clean_exit(self):
        """Setup: dry_run=True; context block completes without exception.
        Expectations: rollback called, commit not called.
        """
        mock_conn = MagicMock()
        manager = ConnectionManager(
            PROFILE, _connection_factory=_factory_returning(mock_conn)
        )

        with manager.connect(dry_run=True):
            pass

        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    def test_dry_run_false_still_commits(self):
        """Setup: dry_run=False (default); context block completes without exception.
        Expectations: commit called, rollback not called.
        """
        mock_conn = MagicMock()
        manager = ConnectionManager(
            PROFILE, _connection_factory=_factory_returning(mock_conn)
        )

        with manager.connect(dry_run=False):
            pass

        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()

    def test_connect_passes_correct_credentials(self):
        """Setup: profile with known credentials.
        Expectations: factory called with matching arguments.
        """
        mock_conn = MagicMock()
        factory = _factory_returning(mock_conn)
        manager = ConnectionManager(PROFILE, _connection_factory=factory)

        with manager.connect():
            pass

        factory.assert_called_once_with(
            host="localhost",
            port=5432,
            dbname="taiga",
            user="taiga",
            password="secret",
        )
