import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from taigun.cli import app
from taigun.config import ConfigManager, Profile
from taigun.db.epic import EpicWriter
from taigun.db.project import ProjectCreator
from taigun.models import Epic
from taigun.resolver import Resolver

runner = CliRunner()


def unique_slug() -> str:
    return f"test-{uuid.uuid4().hex[:8]}"


def make_config(tmp_path: Path, profile) -> ConfigManager:
    config = ConfigManager(path=tmp_path / "config.toml")
    config.save(profile, name=None)
    return config


@contextmanager
def patch_config(config: ConfigManager):
    with patch("taigun.cli.ConfigManager", return_value=config):
        yield config


class TestProjectsListEmpty:
    def test_no_projects_outputs_nothing(self, tmp_path, test_db_profile, cli_conn):
        """Setup: no projects in test-db (test-db-init does not create any).
        Expectations: exit 0; empty output.
        """
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["projects", "list"])

        assert result.exit_code == 0
        assert result.output == ""


class TestProjectsListWithProjects:
    def test_lists_created_project(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project committed; CLI invoked.
        Expectations: output is exactly `My Project (<slug>)` followed by a newline.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("My Project", slug, "admin")
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["projects", "list"])

        assert result.exit_code == 0
        assert result.output == f"My Project ({slug})\n"


class TestEpicsListUnknownProject:
    def test_unknown_slug_exits_one(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project slug that does not exist.
        Expectations: exit 1; exact error message naming the slug.
        """
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["epics", "list", "nonexistent"])

        assert result.exit_code == 1
        assert result.output == "Project 'nonexistent' not found\n"


class TestStatusesListWithProject:
    def test_lists_statuses_grouped_by_type(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project committed.
        Expectations: output contains exactly one line per ticket-type header
            ("story:", "task:", "issue:", "epic:").
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create(
            "Test Project", slug, "admin"
        )
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["statuses", "list", slug])

        assert result.exit_code == 0
        lines = result.output.splitlines()
        headers = [
            line for line in lines if line in {"story:", "task:", "issue:", "epic:"}
        ]
        assert headers == ["story:", "task:", "issue:", "epic:"]


class TestEpicsList:
    def test_empty_when_no_epics(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project committed; no epics in it.
        Expectations: exit 0; empty output.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create(
            "Test Project", slug, "admin"
        )
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["epics", "list", slug])

        assert result.exit_code == 0
        assert result.output == ""

    def test_lists_written_epic(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project and one epic written on the test's shared connection.
        Expectations: output contains a line ending with the epic's subject.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create(
            "Test Project", slug, "admin"
        )
        epic_ref = EpicWriter(cli_conn, Resolver(cli_conn)).write(
            Epic(project=slug, subject="Big feature"), "admin"
        )

        config = make_config(tmp_path, test_db_profile)
        with patch_config(config):
            result = runner.invoke(app, ["epics", "list", slug])

        assert result.exit_code == 0
        assert result.output == f"#{epic_ref}  Big feature\n"


class TestProfileFlagOnListCommands:
    def test_projects_list_uses_named_profile(
        self, tmp_path, test_db_profile, cli_conn
    ):
        """Setup: 'work' profile with test-db creds; bad default profile.
        Expectations: `projects list --profile work` exits 0.
        """
        config = ConfigManager(path=tmp_path / "config.toml")
        bad_default = Profile(
            "nonexistent-host", 5432, "taiga", "taiga", "taiga", "admin"
        )
        config.save(bad_default, name=None)
        config.save(test_db_profile, name="work")

        with patch_config(config):
            result = runner.invoke(app, ["projects", "list", "--profile", "work"])

        assert result.exit_code == 0

    def test_epics_list_uses_named_profile(self, tmp_path, test_db_profile, cli_conn):
        """Setup: 'work' profile with test-db creds; project committed.
        Expectations: `epics list <slug> --profile work` exits 0.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create(
            "Test Project", slug, "admin"
        )
        config = ConfigManager(path=tmp_path / "config.toml")
        bad_default = Profile(
            "nonexistent-host", 5432, "taiga", "taiga", "taiga", "admin"
        )
        config.save(bad_default, name=None)
        config.save(test_db_profile, name="work")

        with patch_config(config):
            result = runner.invoke(app, ["epics", "list", slug, "--profile", "work"])

        assert result.exit_code == 0

    def test_statuses_list_uses_named_profile(
        self, tmp_path, test_db_profile, cli_conn
    ):
        """Setup: 'work' profile with test-db creds; project committed.
        Expectations: `statuses list <slug> --profile work` exits 0.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create(
            "Test Project", slug, "admin"
        )
        config = ConfigManager(path=tmp_path / "config.toml")
        bad_default = Profile(
            "nonexistent-host", 5432, "taiga", "taiga", "taiga", "admin"
        )
        config.save(bad_default, name=None)
        config.save(test_db_profile, name="work")

        with patch_config(config):
            result = runner.invoke(app, ["statuses", "list", slug, "--profile", "work"])

        assert result.exit_code == 0
