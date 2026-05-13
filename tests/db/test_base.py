import datetime

import pytest

from taigun.db.base import BaseWriter
from taigun.db.story import StoryWriter
from taigun.models import Story
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

    def test_resolve_common_returns_expected_tuple(self, real_conn):
        """Setup: project exists; story with no status override.
        Expectations: _resolve_common returns (project_id, owner_id, status_id, now)
            with positive ids and a timezone-aware datetime.
        """
        project_id = make_project(real_conn)
        writer = StubWriter(real_conn, Resolver(real_conn))
        ticket = Story(project="test-project", subject="Test")

        pid, owner_id, status_id, now = writer._resolve_common(ticket, "admin")

        assert pid == project_id
        assert isinstance(owner_id, int) and owner_id > 0
        assert isinstance(status_id, int) and status_id > 0
        assert isinstance(now, datetime.datetime)
        assert now.tzinfo is not None

    def test_allocate_and_set_ref_returns_positive_ref(self, real_conn):
        """Setup: project exists; write a story (exercises _allocate_and_set_ref via
            the concrete writer path, since allocating requires an existing row).
        Expectations: returned ref is a positive int.
        """
        make_project(real_conn)
        writer = StoryWriter(real_conn, Resolver(real_conn))

        ref = writer.write(Story(project="test-project", subject="Hello"), "admin")

        assert isinstance(ref, int) and ref > 0
