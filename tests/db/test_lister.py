"""Integration tests for Lister.

Tests that don't need a project setup (empty list_projects) sit outside any
xfail; tests that depend on ProjectCreator working sit under an xfail until
its bugs are fixed in ticket 023.
"""
import pytest

from taigun.db.epic import EpicWriter
from taigun.db.lister import Lister
from taigun.db.project import ProjectCreator
from taigun.models import Epic
from taigun.resolver import Resolver

from factories import make_project


class TestListProjectsEmpty:
    def test_returns_empty_list_when_no_projects(self, real_conn):
        """Setup: test-db-init does not create any projects.
        Expectations: list_projects returns an empty list.
        """
        projects = Lister(real_conn).list_projects()

        assert projects == []


class TestListProjects:
    def test_returns_name_slug_pair_after_create(self, real_conn):
        """Setup: one project created.
        Expectations: list_projects returns exactly [(name, slug)].
        """
        make_project(real_conn, name="My Project", slug="my-project")

        projects = Lister(real_conn).list_projects()

        assert projects == [("My Project", "my-project")]

    def test_ordered_by_name(self, real_conn):
        """Setup: three projects with names that sort to a known order.
        Expectations: list_projects returns them sorted by name ascending.
        """
        resolver = Resolver(real_conn)
        for name, slug in [("Zeta", "zeta"), ("Alpha", "alpha"), ("Mu", "mu")]:
            ProjectCreator(real_conn, resolver).create(name, slug, "admin")

        names = [name for name, _ in Lister(real_conn).list_projects()]

        assert names == ["Alpha", "Mu", "Zeta"]


class TestListEpics:
    def test_returns_empty_list_when_project_has_no_epics(self, real_conn):
        """Setup: project with no epics written.
        Expectations: list_epics returns an empty list.
        """
        project_id = make_project(real_conn)

        epics = Lister(real_conn).list_epics(project_id)

        assert epics == []

    def test_returns_ref_subject_pair_after_write(self, real_conn):
        """Setup: project + one epic written.
        Expectations: list_epics returns [(ref, subject)].
        """
        project_id = make_project(real_conn)
        ref = EpicWriter(real_conn, Resolver(real_conn)).write(
            Epic(project="test-project", subject="Big feature"), "admin"
        )

        epics = Lister(real_conn).list_epics(project_id)

        assert epics == [(ref, "Big feature")]

    def test_ordered_by_ref(self, real_conn):
        """Setup: project + three epics written in succession.
        Expectations: list_epics returns them in ascending ref order.
        """
        project_id = make_project(real_conn)
        writer = EpicWriter(real_conn, Resolver(real_conn))
        ref_a = writer.write(Epic(project="test-project", subject="A"), "admin")
        ref_b = writer.write(Epic(project="test-project", subject="B"), "admin")
        ref_c = writer.write(Epic(project="test-project", subject="C"), "admin")

        epics = Lister(real_conn).list_epics(project_id)

        assert [ref for ref, _ in epics] == [ref_a, ref_b, ref_c]


class TestListStatuses:
    def test_returns_entries_for_all_four_types(self, real_conn):
        """Setup: project from default kanban template.
        Expectations: list_statuses returns a dict with non-empty lists for
            'story', 'task', 'issue', and 'epic'.
        """
        project_id = make_project(real_conn)

        statuses = Lister(real_conn).list_statuses(project_id)

        assert set(statuses.keys()) == {"story", "task", "issue", "epic"}
        for ticket_type in statuses:
            assert statuses[ticket_type], f"no statuses for {ticket_type}"

    def test_marks_closed_status_correctly(self, real_conn):
        """Setup: project from default kanban template ('Done' is a closed
            status; 'New' is not closed).
        Expectations: list_statuses['story'] contains ('Done', True) and
            ('New', False).
        """
        project_id = make_project(real_conn)

        statuses = Lister(real_conn).list_statuses(project_id)

        assert ("Done", True) in statuses["story"]
        assert ("New", False) in statuses["story"]
