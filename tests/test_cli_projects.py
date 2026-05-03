from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from taigun.cli import app
from taigun.config import ConfigManager, Profile
from taigun.db.project import ProjectExistsError
from taigun.exceptions import ResolveError

runner = CliRunner()

PROFILE = Profile(
    host="localhost",
    port=5432,
    database="taiga",
    username="taiga",
    password="secret",
    acting_user="admin",
)


def make_config(tmp_path: Path) -> ConfigManager:
    config = ConfigManager(path=tmp_path / "config.toml")
    config.save(PROFILE, name=None)
    return config


@contextmanager
def mock_create(config: ConfigManager, create_return=(101, "my-project"), create_error=None):
    """Patch the database layer for projects create. Yields (mock_creator, mock_cm)."""
    mock_creator = MagicMock()
    if create_error:
        mock_creator.return_value.create.side_effect = create_error
    else:
        mock_creator.return_value.create.return_value = create_return

    with patch("taigun.cli.ConfigManager", return_value=config), \
         patch("taigun.cli.ConnectionManager") as mock_cm, \
         patch("taigun.cli.Resolver"), \
         patch("taigun.cli.ProjectCreator", mock_creator):

        mock_cm.return_value.connect.return_value.__enter__.return_value = MagicMock()
        mock_cm.return_value.connect.return_value.__exit__.return_value = False

        yield mock_creator, mock_cm


class TestProjectsCreate:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    def test_success_output(self, config):
        """Setup: create returns (101, 'my-project').
        Expectations: exact output is 'Created project #101: my-project\\n'; exit 0.
        """
        with mock_create(config):
            result = runner.invoke(app, ["projects", "create", "My Project", "my-project"])

        assert result.exit_code == 0
        assert result.output == "Created project #101: my-project\n"

    def test_calls_create_with_name_slug_and_acting_user(self, config):
        """Setup: invoke with name 'My Project' and slug 'my-project'.
        Expectations: ProjectCreator.create called with those args + 'admin' from profile.
        """
        with mock_create(config) as (creator, _):
            runner.invoke(app, ["projects", "create", "My Project", "my-project"])

        creator.return_value.create.assert_called_once_with("My Project", "my-project", "admin")

    def test_exits_nonzero_when_slug_exists(self, config):
        """Setup: ProjectCreator.create raises ProjectExistsError.
        Expectations: exit code 1; error message in output.
        """
        with mock_create(
            config,
            create_error=ProjectExistsError("Project with slug 'my-project' already exists"),
        ):
            result = runner.invoke(app, ["projects", "create", "My Project", "my-project"])

        assert result.exit_code == 1
        assert result.output == "Project with slug 'my-project' already exists\n"

    def test_exits_nonzero_when_resolve_fails(self, config):
        """Setup: ProjectCreator.create raises ResolveError.
        Expectations: exit code 1; error message in output.
        """
        with mock_create(config, create_error=ResolveError("User 'admin' not found")):
            result = runner.invoke(app, ["projects", "create", "My Project", "my-project"])

        assert result.exit_code == 1
        assert result.output == "User 'admin' not found\n"

    def test_profile_flag_loads_named_profile(self, tmp_path):
        """Setup: --profile work; work profile has acting_user 'workuser'.
        Expectations: ConnectionManager called with the work profile (host=workhost).
        """
        config = make_config(tmp_path)
        work_profile = Profile("workhost", 5432, "taiga", "taiga", "secret", "workuser")
        config.save(work_profile, name="work")

        with mock_create(config) as (_, mock_cm):
            runner.invoke(
                app,
                ["projects", "create", "--profile", "work", "Work Project", "work-proj"],
            )

        used_profile = mock_cm.call_args.args[0]
        assert used_profile.host == "workhost"
        assert used_profile.acting_user == "workuser"
