import logging

import pytest

from taigun.exceptions import ResolveError
from taigun.resolver import Resolver

from factories import make_project


class TestResolveUser:
    def test_returns_user_id(self, real_conn):
        """Setup: admin user created by test-db-init.
        Expectations: resolve_user('admin') returns a positive int.
        """
        admin_id = Resolver(real_conn).resolve_user("admin")

        assert isinstance(admin_id, int) and admin_id > 0

    def test_not_found_raises(self, real_conn):
        """Setup: no user with that username.
        Expectations: ResolveError raised with the username in the message.
        """
        with pytest.raises(ResolveError, match="nobody"):
            Resolver(real_conn).resolve_user("nobody")


class TestResolveContentType:
    def test_returns_content_type_id(self, real_conn):
        """Setup: django_content_type populated by Taiga migrations.
        Expectations: resolve_content_type returns a positive int.
        """
        ct_id = Resolver(real_conn).resolve_content_type("userstories", "userstory")

        assert isinstance(ct_id, int) and ct_id > 0

    def test_not_found_raises(self, real_conn):
        """Setup: no content type with that label/model.
        Expectations: ResolveError raised.
        """
        with pytest.raises(ResolveError):
            Resolver(real_conn).resolve_content_type("nonexistent", "nothing")

    def test_result_is_cached(self, real_conn):
        """Setup: resolver instance.
        Expectations: repeated calls return the same value.
        """
        resolver = Resolver(real_conn)

        first = resolver.resolve_content_type("userstories", "userstory")
        second = resolver.resolve_content_type("userstories", "userstory")

        assert first == second

    def test_different_keys_return_different_ids(self, real_conn):
        """Setup: resolver instance.
        Expectations: different (app_label, model) keys return different IDs.
        """
        resolver = Resolver(real_conn)

        a = resolver.resolve_content_type("userstories", "userstory")
        b = resolver.resolve_content_type("epics", "epic")

        assert a != b


class TestResolveProjectNotFound:
    def test_not_found_raises(self, real_conn):
        """Setup: no project with that slug.
        Expectations: ResolveError raised with the slug in the message.
        """
        with pytest.raises(ResolveError, match="nonexistent"):
            Resolver(real_conn).resolve_project("nonexistent")


@pytest.mark.xfail(reason="ticket 023: project setup depends on ProjectCreator SQL")
class TestResolveProject:
    def test_returns_project_id(self, real_conn):
        """Setup: project with slug 'test-project' created via make_project.
        Expectations: resolve_project returns the same id make_project returned.
        """
        expected_id = make_project(real_conn, slug="test-project")

        assert Resolver(real_conn).resolve_project("test-project") == expected_id


@pytest.mark.xfail(reason="ticket 023: project setup depends on ProjectCreator SQL")
class TestResolveStatus:
    def test_returns_status_id_for_known_kanban_name(self, real_conn):
        """Setup: project from default kanban template ('New' is a known story status).
        Expectations: resolve_status returns a positive id for the known name.
        """
        project_id = make_project(real_conn)

        status_id = Resolver(real_conn).resolve_status(project_id, "New", "story")

        assert isinstance(status_id, int) and status_id > 0

    def test_not_found_raises(self, real_conn):
        """Setup: project exists; no status named 'Bogus'.
        Expectations: ResolveError raised.
        """
        project_id = make_project(real_conn)

        with pytest.raises(ResolveError):
            Resolver(real_conn).resolve_status(project_id, "Bogus", "story")

    def test_invalid_ticket_type_raises(self, real_conn):
        """Setup: project exists.
        Expectations: an unknown ticket_type raises ResolveError.
        """
        project_id = make_project(real_conn)

        with pytest.raises(ResolveError):
            Resolver(real_conn).resolve_status(project_id, "New", "badtype")

    @pytest.mark.parametrize("ticket_type", ["story", "task", "issue", "epic"])
    def test_resolves_for_each_ticket_type(self, real_conn, ticket_type):
        """Setup: project from default kanban template ('New' is a status in every type).
        Expectations: resolve_status returns a positive id for each type.
        """
        project_id = make_project(real_conn)

        status_id = Resolver(real_conn).resolve_status(project_id, "New", ticket_type)

        assert isinstance(status_id, int) and status_id > 0


@pytest.mark.xfail(reason="ticket 023: project setup depends on ProjectCreator SQL")
class TestResolveDefaultStatus:
    def test_returns_positive_id(self, real_conn):
        """Setup: project with default story status set.
        Expectations: resolve_default_status returns a positive id.
        """
        project_id = make_project(real_conn)

        status_id = Resolver(real_conn).resolve_default_status(project_id, "story")

        assert isinstance(status_id, int) and status_id > 0

    def test_invalid_ticket_type_raises(self, real_conn):
        """Setup: any project.
        Expectations: an unknown ticket_type raises ResolveError.
        """
        project_id = make_project(real_conn)

        with pytest.raises(ResolveError):
            Resolver(real_conn).resolve_default_status(project_id, "badtype")

    @pytest.mark.parametrize("ticket_type", ["story", "task", "issue", "epic"])
    def test_resolves_for_each_ticket_type(self, real_conn, ticket_type):
        """Setup: project with default status for each type.
        Expectations: resolve_default_status returns a positive id for each.
        """
        project_id = make_project(real_conn)

        status_id = Resolver(real_conn).resolve_default_status(project_id, ticket_type)

        assert isinstance(status_id, int) and status_id > 0


@pytest.mark.xfail(reason="ticket 023: resolve_default_status queries non-existent `is_default` column")
class TestResolveDefaultStatusForNonexistentProject:
    def test_raises_resolve_error(self, real_conn):
        """Setup: a project ID that does not exist.
        Expectations: ResolveError raised.
        """
        with pytest.raises(ResolveError):
            Resolver(real_conn).resolve_default_status(99999, "story")


@pytest.mark.xfail(reason="ticket 023: project setup depends on ProjectCreator SQL")
class TestResolvePriority:
    def test_returns_id_for_known_priority_name(self, real_conn):
        """Setup: project from default kanban template ('Normal' is a known priority).
        Expectations: resolve_priority returns a positive id for the known name.
        """
        project_id = make_project(real_conn)

        priority_id = Resolver(real_conn).resolve_priority(project_id, "Normal")

        assert isinstance(priority_id, int) and priority_id > 0

    def test_falls_back_to_default_on_unknown_name(self, real_conn):
        """Setup: project exists; unknown priority name passed.
        Expectations: resolve_priority returns a positive id (the default).
        """
        project_id = make_project(real_conn)

        priority_id = Resolver(real_conn).resolve_priority(project_id, "Bogus")

        assert isinstance(priority_id, int) and priority_id > 0

    def test_fallback_logs_warning(self, real_conn, caplog):
        """Setup: unknown priority name.
        Expectations: a warning naming the unknown value is logged.
        """
        project_id = make_project(real_conn)
        caplog.set_level(logging.WARNING)

        Resolver(real_conn).resolve_priority(project_id, "Bogus")

        assert any("Bogus" in record.message for record in caplog.records)

    def test_none_name_returns_default_without_warning(self, real_conn, caplog):
        """Setup: name=None.
        Expectations: returns the default; no warning emitted.
        """
        project_id = make_project(real_conn)
        caplog.set_level(logging.WARNING)

        priority_id = Resolver(real_conn).resolve_priority(project_id, None)

        assert isinstance(priority_id, int) and priority_id > 0
        assert not caplog.records


@pytest.mark.xfail(reason="ticket 023: project setup depends on ProjectCreator SQL")
class TestResolveIssueType:
    def test_returns_id_for_known_issue_type(self, real_conn):
        """Setup: project from default kanban template ('Bug' is a known type).
        Expectations: resolve_issue_type returns a positive id.
        """
        project_id = make_project(real_conn)

        type_id = Resolver(real_conn).resolve_issue_type(project_id, "Bug")

        assert isinstance(type_id, int) and type_id > 0

    def test_falls_back_to_default_on_unknown_name(self, real_conn):
        project_id = make_project(real_conn)

        type_id = Resolver(real_conn).resolve_issue_type(project_id, "Bogus")

        assert isinstance(type_id, int) and type_id > 0

    def test_fallback_logs_warning(self, real_conn, caplog):
        project_id = make_project(real_conn)
        caplog.set_level(logging.WARNING)

        Resolver(real_conn).resolve_issue_type(project_id, "Bogus")

        assert any("Bogus" in record.message for record in caplog.records)

    def test_none_name_returns_default_without_warning(self, real_conn, caplog):
        project_id = make_project(real_conn)
        caplog.set_level(logging.WARNING)

        type_id = Resolver(real_conn).resolve_issue_type(project_id, None)

        assert isinstance(type_id, int) and type_id > 0
        assert not caplog.records


@pytest.mark.xfail(reason="ticket 023: project setup depends on ProjectCreator SQL")
class TestResolveSeverity:
    def test_returns_id_for_known_severity(self, real_conn):
        """Setup: project from default kanban template ('Normal' is a known severity).
        Expectations: resolve_severity returns a positive id.
        """
        project_id = make_project(real_conn)

        sev_id = Resolver(real_conn).resolve_severity(project_id, "Normal")

        assert isinstance(sev_id, int) and sev_id > 0

    def test_falls_back_to_default_on_unknown_name(self, real_conn):
        project_id = make_project(real_conn)

        sev_id = Resolver(real_conn).resolve_severity(project_id, "Bogus")

        assert isinstance(sev_id, int) and sev_id > 0

    def test_fallback_logs_warning(self, real_conn, caplog):
        project_id = make_project(real_conn)
        caplog.set_level(logging.WARNING)

        Resolver(real_conn).resolve_severity(project_id, "Bogus")

        assert any("Bogus" in record.message for record in caplog.records)

    def test_none_name_returns_default_without_warning(self, real_conn, caplog):
        project_id = make_project(real_conn)
        caplog.set_level(logging.WARNING)

        sev_id = Resolver(real_conn).resolve_severity(project_id, None)

        assert isinstance(sev_id, int) and sev_id > 0
        assert not caplog.records


@pytest.mark.xfail(reason="ticket 023: resolve_milestone queries non-existent `projects_milestone` table (should be milestones_milestone)")
class TestResolveMilestoneNotFound:
    def test_not_found_raises(self, real_conn):
        """Setup: no milestone of that name in any project.
        Expectations: ResolveError raised with the name in the message.
        """
        with pytest.raises(ResolveError, match="Sprint 99"):
            Resolver(real_conn).resolve_milestone(99999, "Sprint 99")


class TestResolveStoryNotFound:
    def test_not_found_raises(self, real_conn):
        """Setup: no story with that ref in any project.
        Expectations: ResolveError raised.
        """
        with pytest.raises(ResolveError, match="ref #999"):
            Resolver(real_conn).resolve_story(99999, 999)


class TestResolveEpicNotFound:
    def test_not_found_raises(self, real_conn):
        """Setup: no epic with that ref in any project.
        Expectations: ResolveError raised.
        """
        with pytest.raises(ResolveError, match="ref #999"):
            Resolver(real_conn).resolve_epic(99999, 999)
