from unittest.mock import MagicMock

from taigun.db.base import BaseWriter


class StubWriter(BaseWriter):
    _ticket_type = "story"
    _content_type = ("userstories", "userstory")
    _table = "userstories_userstory"

    def write(self, ticket, acting_user: str) -> int:
        pass


def make_writer():
    mock_conn = MagicMock()
    mock_resolver = MagicMock()
    mock_resolver.resolve_status.return_value = 2
    mock_resolver.resolve_default_status.return_value = 2

    return StubWriter(mock_conn, mock_resolver), mock_resolver


class TestBaseWriterResolveStatus:
    def test_resolves_status_when_set(self):
        """Setup: status name provided.
        Expectations: resolve_status called with project_id, name, and ticket_type;
        resolve_default_status not called.
        """
        writer, mock_resolver = make_writer()

        writer._resolve_status(1, "In Progress")

        mock_resolver.resolve_status.assert_called_once_with(1, "In Progress", "story")
        mock_resolver.resolve_default_status.assert_not_called()

    def test_resolves_default_status_when_not_set(self):
        """Setup: status is None.
        Expectations: resolve_default_status called with project_id and ticket_type;
        resolve_status not called.
        """
        writer, mock_resolver = make_writer()

        writer._resolve_status(1, None)

        mock_resolver.resolve_default_status.assert_called_once_with(1, "story")
        mock_resolver.resolve_status.assert_not_called()
