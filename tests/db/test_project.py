import pytest

from taigun.db.lister import Lister
from taigun.db.project import ProjectCreator, ProjectExistsError
from taigun.resolver import Resolver


@pytest.mark.xfail(reason="ticket 023: ProjectCreator SQL not yet verified against real schema")
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
