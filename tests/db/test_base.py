import pytest

from taigun.db.base import BaseWriter
from taigun.resolver import Resolver

from factories import make_project


class StubWriter(BaseWriter):
    _ticket_type = "story"
    _content_type = ("userstories", "userstory")
    _table = "userstories_userstory"

    def write(self, ticket, acting_user: str) -> int:
        pass


@pytest.mark.xfail(reason="ticket 023: project setup depends on ProjectCreator SQL")
class TestBaseWriterResolveStatus:
    def test_resolves_named_status_returns_positive_id(self, real_conn):
        """Setup: project with default kanban template ('New' is a known story status).
        Expectations: _resolve_status returns a positive id for the known name.
        """
        project_id = make_project(real_conn)
        writer = StubWriter(real_conn, Resolver(real_conn))

        status_id = writer._resolve_status(project_id, "New")

        assert isinstance(status_id, int) and status_id > 0

    def test_resolves_default_status_when_name_none(self, real_conn):
        """Setup: project with a default story status configured.
        Expectations: _resolve_status(None) returns a positive id (the project's default).
        """
        project_id = make_project(real_conn)
        writer = StubWriter(real_conn, Resolver(real_conn))

        status_id = writer._resolve_status(project_id, None)

        assert isinstance(status_id, int) and status_id > 0
