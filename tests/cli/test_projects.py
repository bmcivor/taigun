import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from taigun.cli import app
from taigun.config import ConfigManager, Profile
from taigun.db.project import ProjectCreator
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


class TestProjectsCreate:
    def test_success_output(self, tmp_path, test_db_profile, cli_conn):
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
        assert lines[0].startswith("Created project #") and lines[0].endswith(
            f": {slug}"
        )

    def test_exits_nonzero_when_slug_exists(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project with that slug already exists.
        Expectations: exit 1; output is exactly the ProjectExistsError message.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Existing", slug, "admin")
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["projects", "create", "Duplicate", slug])

        assert result.exit_code == 1
        assert result.output == f"Project with slug '{slug}' already exists\n"

    def test_unknown_acting_user_exits_nonzero(
        self, tmp_path, test_db_profile, cli_conn
    ):
        """Setup: profile with acting_user='nobody' (does not exist).
        Expectations: exit 1; output mentions the unknown user.
        """
        bad_user_profile = Profile(
            host=test_db_profile.host,
            port=test_db_profile.port,
            database=test_db_profile.database,
            username=test_db_profile.username,
            password=test_db_profile.password,
            acting_user="nobody",
        )
        config = make_config(tmp_path, bad_user_profile)

        with patch_config(config):
            result = runner.invoke(app, ["projects", "create", "Test", unique_slug()])

        assert result.exit_code == 1
        assert result.output == "User 'nobody' not found\n"

    def test_profile_flag_uses_named_profile(self, tmp_path, test_db_profile, cli_conn):
        """Setup: 'work' profile with test-db creds; bad default profile.
        Expectations: `projects create ... --profile work` exits 0.
        """
        config = ConfigManager(path=tmp_path / "config.toml")
        bad_default = Profile(
            "nonexistent-host", 5432, "taiga", "taiga", "taiga", "admin"
        )
        config.save(bad_default, name=None)
        config.save(test_db_profile, name="work")

        with patch_config(config):
            result = runner.invoke(
                app,
                ["projects", "create", "--profile", "work", "Test", unique_slug()],
            )

        assert result.exit_code == 0


class TestProjectsUpdate:
    def test_updates_name_and_description(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project created; run projects update with --name and
            --description.
        Expectations: exit 0; DB row reflects both new values; success line.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Original", slug, "admin")
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(
                app,
                [
                    "projects",
                    "update",
                    slug,
                    "--name",
                    "Renamed",
                    "--description",
                    "New body",
                ],
            )

        assert result.exit_code == 0
        assert result.output == f"Updated project '{slug}'\n"

        with cli_conn.cursor() as cur:
            cur.execute(
                "SELECT name, description FROM projects_project WHERE slug = %s",
                (slug,),
            )
            row = cur.fetchone()

        assert row == ("Renamed", "New body")

    def test_updates_only_provided_field(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project has name='Original' and description=''; update with
            --description only.
        Expectations: name stays 'Original'; description becomes 'Just docs'.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Original", slug, "admin")
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(
                app,
                ["projects", "update", slug, "--description", "Just docs"],
            )

        assert result.exit_code == 0

        with cli_conn.cursor() as cur:
            cur.execute(
                "SELECT name, description FROM projects_project WHERE slug = %s",
                (slug,),
            )
            row = cur.fetchone()

        assert row == ("Original", "Just docs")

    def test_no_flags_exits_nonzero(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project exists but user runs update with no flags.
        Expectations: exit 1; error line explains that nothing was passed.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Original", slug, "admin")
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(app, ["projects", "update", slug])

        assert result.exit_code == 1
        assert result.output == "Nothing to update: pass --name and/or --description.\n"

    def test_unknown_slug_exits_nonzero(self, tmp_path, test_db_profile, cli_conn):
        """Setup: no project with that slug.
        Expectations: exit 1; error names the missing slug.
        """
        slug = unique_slug()
        config = make_config(tmp_path, test_db_profile)

        with patch_config(config):
            result = runner.invoke(
                app,
                ["projects", "update", slug, "--name", "x"],
            )

        assert result.exit_code == 1
        assert result.output == f"project with slug '{slug}' not found\n"
