import psycopg2
from contextlib import contextmanager
from typing import Callable, Generator, Optional

from taigun.config import Profile


class ConnectionManager:
    """Manages a PostgreSQL connection for a single taigun operation.

    Opens a connection from a Profile, commits on clean exit, and rolls
    back on exception. psycopg2 errors are surfaced with a clear message.

    ``_connection_factory`` is a test seam: production always leaves it None
    and falls back to ``psycopg2.connect``. The CLI test fixture injects a
    factory that returns a savepoint-scoped wrapper around the test's open
    transaction so CLI writes stay visible to the test without committing.
    """

    def __init__(
        self,
        config: Profile,
        *,
        _connection_factory: Optional[Callable[..., psycopg2.extensions.connection]] = None,
    ) -> None:
        self._config = config
        self._connect = _connection_factory or psycopg2.connect

    @contextmanager
    def connect(self, dry_run: bool = False) -> Generator[psycopg2.extensions.connection, None, None]:
        """Open a database connection as a context manager.

        Args:
            dry_run: If True, rollback instead of commit on clean exit.

        Yields:
            An open psycopg2 connection.

        Raises:
            SystemExit: If the connection cannot be established.
        """
        try:
            conn = self._connect(
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
            if dry_run:
                conn.rollback()
            else:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
