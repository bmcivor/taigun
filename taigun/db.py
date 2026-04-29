import psycopg2
from contextlib import contextmanager
from typing import Generator

from taigun.config import Profile


class ConnectionManager:
    """Manages a PostgreSQL connection for a single taigun operation.

    Opens a connection from a Profile, commits on clean exit, and rolls
    back on exception. psycopg2 errors are surfaced with a clear message.
    """

    def __init__(self, config: Profile) -> None:
        self._config = config

    @contextmanager
    def connect(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Open a database connection as a context manager.

        Yields:
            An open psycopg2 connection.

        Raises:
            SystemExit: If the connection cannot be established.
        """
        try:
            conn = psycopg2.connect(
                host=self._config.host,
                port=self._config.port,
                dbname=self._config.database,
                user=self._config.username,
                password=self._config.password,
            )
        except psycopg2.OperationalError as e:
            raise SystemExit(f"Could not connect to database: {e}")

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
