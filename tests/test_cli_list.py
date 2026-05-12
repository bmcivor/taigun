import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import psycopg2
import pytest
from typer.testing import CliRunner

from taigun.cli import app
from taigun.config import ConfigManager
from taigun.db.project import ProjectCreator
from taigun.resolver import Resolver

runner = CliRunner()


def unique_slug() -> str:
    return f"test-{uuid.uuid4().hex[:8]}"


def make_config(tmp_path: Path, profile) -> ConfigManager:
    config = ConfigManager(path=tmp_path / "config.toml")
    config.save(profile, name=None)
    return config


def commit_project(profile, slug: str, name: str = "Test Project") -> int:
    """Create a project via ProjectCreator in its own committed connection."""
    conn = psycopg2.connect(
        host=profile.host,
        port=profile.port,
        dbname=profile.database,
        user=profile.username,
        password=profile.password,
    )
    try:
        project_id, _ = ProjectCreator(conn, Resolver(conn)).create(name, slug, "admin")
        conn.commit()
        return project_id
    finally:
        conn.close()


@contextmanager
def patch_config(config: ConfigManager):
    with patch("taigun.cli.ConfigManager", return_value=config):
        yield config


class TestProjectsListEmpty:
    def test_no_projects_outputs_nothing(self, tmp_path, test_db_profile):
        """Setup: no projects in test-db (test-db-init does not create any).
        Expectations: exit 0; empty output.
        """
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["projects", "list"])

        assert result.exit_code == 0
        assert result.output == ""


@pytest.mark.xfail(reason="ticket 023: requires ProjectCreator to work for setup")
class TestProjectsListWithProjects:
    def test_lists_created_project(self, tmp_path, test_db_profile):
        """Setup: project committed; CLI invoked.
        Expectations: output is exactly `My Project (<slug>)` followed by a newline.
        """
        slug = unique_slug()
        commit_project(test_db_profile, slug, name="My Project")
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["projects", "list"])

        assert result.exit_code == 0
        assert result.output == f"My Project ({slug})\n"


class TestEpicsListUnknownProject:
    def test_unknown_slug_exits_one(self, tmp_path, test_db_profile):
        """Setup: project slug that does not exist.
        Expectations: exit 1; exact error message naming the slug.
        """
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["epics", "list", "nonexistent"])

        assert result.exit_code == 1
        assert result.output == "Project 'nonexistent' not found\n"


@pytest.mark.xfail(reason="ticket 023: requires ProjectCreator to work for setup")
class TestStatusesListWithProject:
    def test_lists_statuses_grouped_by_type(self, tmp_path, test_db_profile):
        """Setup: project committed.
        Expectations: output contains exactly one line per ticket-type header
            ("story:", "task:", "issue:", "epic:").
        """
        slug = unique_slug()
        commit_project(test_db_profile, slug)
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["statuses", "list", slug])

        assert result.exit_code == 0
        lines = result.output.splitlines()
        headers = [line for line in lines if line in {"story:", "task:", "issue:", "epic:"}]
        assert headers == ["story:", "task:", "issue:", "epic:"]
