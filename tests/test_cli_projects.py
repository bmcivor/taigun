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


@pytest.mark.xfail(reason="ticket 023: ProjectCreator SQL not yet verified against real schema")
class TestProjectsCreate:
    def test_success_output(self, tmp_path, test_db_profile):
        """Setup: clean test-db.
        Expectations: output is exactly one line matching
            `Created project #<id>: <slug>` (id is dynamic so use endswith).
        """
        slug = unique_slug()
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["projects", "create", "My Project", slug])

        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert len(lines) == 1
        assert lines[0].startswith("Created project #") and lines[0].endswith(f": {slug}")

    def test_exits_nonzero_when_slug_exists(self, tmp_path, test_db_profile):
        """Setup: project with that slug already exists.
        Expectations: exit 1; output is exactly the ProjectExistsError message.
        """
        slug = unique_slug()
        commit_project(test_db_profile, slug)
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["projects", "create", "Duplicate", slug])

        assert result.exit_code == 1
        assert result.output == f"Project with slug '{slug}' already exists\n"
