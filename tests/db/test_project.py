import pytest

from taigun.db import RefAllocator
from taigun.db.lister import Lister
from taigun.db.project import ProjectCreator, ProjectExistsError
from taigun.resolver import Resolver


class TestProjectCreator:
    def test_returns_id_and_slug(self, real_conn):
        """Setup: clean test-db with default ProjectTemplate.
        Expectations: create returns a positive id and the slug passed in.
        """
        creator = ProjectCreator(real_conn, Resolver(real_conn))

        project_id, slug = creator.create("My Project", "my-project", "admin")

        assert isinstance(project_id, int) and project_id > 0
        assert slug == "my-project"

    def test_lister_finds_created_project(self, real_conn):
        """Setup: create a project.
        Expectations: Lister.list_projects contains (name, slug) of the new project.
        """
        ProjectCreator(real_conn, Resolver(real_conn)).create("My Project", "my-project", "admin")

        projects = Lister(real_conn).list_projects()

        assert ("My Project", "my-project") in projects

    def test_duplicate_slug_raises(self, real_conn):
        """Setup: project with slug 'my-project' already exists.
        Expectations: second create with same slug raises ProjectExistsError.
        """
        resolver = Resolver(real_conn)
        ProjectCreator(real_conn, resolver).create("First", "my-project", "admin")

        with pytest.raises(ProjectExistsError, match="my-project"):
            ProjectCreator(real_conn, resolver).create("Second", "my-project", "admin")

    def test_creates_statuses_for_all_four_types(self, real_conn):
        """Setup: create a project.
        Expectations: Lister.list_statuses returns non-empty lists for story, task,
            issue, and epic for the new project.
        """
        project_id, _ = ProjectCreator(real_conn, Resolver(real_conn)).create(
            "My Project", "my-project", "admin"
        )

        statuses = Lister(real_conn).list_statuses(project_id)

        for ticket_type in ("story", "task", "issue", "epic"):
            assert statuses[ticket_type], f"no statuses materialised for {ticket_type}"

    def test_priorities_resolvable_after_create(self, real_conn):
        """Setup: create a project (default kanban template includes 'Normal' priority).
        Expectations: Resolver.resolve_priority(id, 'Normal') returns a positive id.
        """
        project_id, _ = ProjectCreator(real_conn, Resolver(real_conn)).create(
            "My Project", "my-project", "admin"
        )

        priority_id = Resolver(real_conn).resolve_priority(project_id, "Normal")

        assert isinstance(priority_id, int) and priority_id > 0

    def test_severities_resolvable_after_create(self, real_conn):
        """Setup: create a project (default kanban template includes 'Normal' severity).
        Expectations: Resolver.resolve_severity(id, 'Normal') returns a positive id.
        """
        project_id, _ = ProjectCreator(real_conn, Resolver(real_conn)).create(
            "My Project", "my-project", "admin"
        )

        severity_id = Resolver(real_conn).resolve_severity(project_id, "Normal")

        assert isinstance(severity_id, int) and severity_id > 0

    def test_issue_types_resolvable_after_create(self, real_conn):
        """Setup: create a project (default kanban template includes 'Bug' issue type).
        Expectations: Resolver.resolve_issue_type(id, 'Bug') returns a positive id.
        """
        project_id, _ = ProjectCreator(real_conn, Resolver(real_conn)).create(
            "My Project", "my-project", "admin"
        )

        type_id = Resolver(real_conn).resolve_issue_type(project_id, "Bug")

        assert isinstance(type_id, int) and type_id > 0

    def test_ref_sequence_usable_after_create(self, real_conn):
        """Setup: create a project (which creates the references_project<id> sequence).
        Expectations: RefAllocator.allocate against the new project returns a positive ref
            without raising — confirms the sequence exists.
        """
        project_id, _ = ProjectCreator(real_conn, Resolver(real_conn)).create(
            "My Project", "my-project", "admin"
        )
        content_type_id = Resolver(real_conn).resolve_content_type("userstories", "userstory")

        ref = RefAllocator(real_conn).allocate(project_id, 1, content_type_id)

        assert isinstance(ref, int) and ref > 0

    def test_owner_membership_inserted_without_exception(self, real_conn):
        """Setup: create a project; owner membership is inserted as part of creation.
        Expectations: create returns successfully (membership INSERT did not raise).

        Direct verification of the membership row requires a read API which doesn't
        exist; this test documents that the code path runs end-to-end.
        """
        project_id, _ = ProjectCreator(real_conn, Resolver(real_conn)).create(
            "My Project", "my-project", "admin"
        )

        assert isinstance(project_id, int) and project_id > 0
