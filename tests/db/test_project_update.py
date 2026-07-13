import psycopg2.extensions
import pytest

from taigun.db.project import ProjectCreator, ProjectUpdater
from taigun.exceptions import ProjectMissingError
from taigun.resolver import Resolver


class TestProjectUpdater:
    def test_updates_name_and_description(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: project created with 'Original' name.
        Expectations: name and description overwritten in DB.
        """
        ProjectCreator(real_conn, Resolver(real_conn)).create(
            "Original", "test-project", "admin",
        )

        ProjectUpdater(real_conn).update(
            "test-project", name="Renamed", description="New body",
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT name, description FROM projects_project WHERE slug = %s",
                ("test-project",),
            )
            row = cur.fetchone()

        assert row == ("Renamed", "New body")

    def test_only_provided_fields_change(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: project created; update called with description only.
        Expectations: name unchanged; description updated.
        """
        ProjectCreator(real_conn, Resolver(real_conn)).create(
            "Original", "test-project", "admin",
        )

        ProjectUpdater(real_conn).update("test-project", description="Docs only")

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT name, description FROM projects_project WHERE slug = %s",
                ("test-project",),
            )
            row = cur.fetchone()

        assert row == ("Original", "Docs only")

    def test_missing_slug_raises(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: no project with that slug.
        Expectations: ProjectMissingError naming the slug.
        """
        with pytest.raises(ProjectMissingError, match="ghost"):
            ProjectUpdater(real_conn).update("ghost", name="anything")

    def test_no_op_when_all_fields_none(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: project created; update called with all fields None.
        Expectations: no change; no error.
        """
        ProjectCreator(real_conn, Resolver(real_conn)).create(
            "Original", "test-project", "admin",
        )

        ProjectUpdater(real_conn).update("test-project")

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT name FROM projects_project WHERE slug = %s",
                ("test-project",),
            )
            (name,) = cur.fetchone()

        assert name == "Original"
