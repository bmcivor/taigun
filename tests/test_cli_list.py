from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from taigun.cli import app
from taigun.config import ConfigManager, Profile
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
def mock_list(config: ConfigManager, resolve_project_id: int = 1, resolve_error=None):
    """Patch the database layer for list commands. Yields mock_lister."""
    mock_lister_instance = MagicMock()

    with patch("taigun.cli.ConfigManager", return_value=config), \
         patch("taigun.cli.ConnectionManager") as mock_cm, \
         patch("taigun.cli.Resolver") as mock_resolver_cls, \
         patch("taigun.cli.Lister", return_value=mock_lister_instance):

        mock_cm.return_value.connect.return_value.__enter__.return_value = MagicMock()
        mock_cm.return_value.connect.return_value.__exit__.return_value = False

        if resolve_error:
            mock_resolver_cls.return_value.resolve_project.side_effect = resolve_error
        else:
            mock_resolver_cls.return_value.resolve_project.return_value = resolve_project_id

        yield mock_lister_instance


class TestProjectsList:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    def test_output_format(self, config):
        """Setup: two projects returned.
        Expectations: each line is 'name (slug)'; exact output matches.
        """
        with mock_list(config) as lister:
            lister.list_projects.return_value = [("Alpha", "alpha"), ("Beta", "beta")]
            result = runner.invoke(app, ["projects", "list"])

        assert result.exit_code == 0
        assert result.output == "Alpha (alpha)\nBeta (beta)\n"

    def test_empty_list(self, config):
        """Setup: no projects.
        Expectations: no output; exit code 0.
        """
        with mock_list(config) as lister:
            lister.list_projects.return_value = []
            result = runner.invoke(app, ["projects", "list"])

        assert result.exit_code == 0
        assert result.output == ""

    def test_profile_flag(self, tmp_path):
        """Setup: --profile work passed; work profile exists with different host.
        Expectations: ConnectionManager called with the work profile.
        """
        config = make_config(tmp_path)
        work_profile = Profile("workhost", 5432, "taiga", "taiga", "secret", "workuser")
        config.save(work_profile, name="work")

        with mock_list(config) as lister:
            lister.list_projects.return_value = []
            with patch("taigun.cli.ConnectionManager") as mock_cm:
                mock_cm.return_value.connect.return_value.__enter__.return_value = MagicMock()
                mock_cm.return_value.connect.return_value.__exit__.return_value = False
                runner.invoke(app, ["projects", "list", "--profile", "work"])

            used_profile = mock_cm.call_args.args[0]

        assert used_profile.host == "workhost"


class TestEpicsList:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    def test_output_format(self, config):
        """Setup: two epics returned.
        Expectations: each line is '#ref  subject'; exact output matches.
        """
        with mock_list(config) as lister:
            lister.list_epics.return_value = [(1, "First epic"), (2, "Second epic")]
            result = runner.invoke(app, ["epics", "list", "my-project"])

        assert result.exit_code == 0
        assert result.output == "#1  First epic\n#2  Second epic\n"

    def test_empty_list(self, config):
        """Setup: no epics in project.
        Expectations: no output; exit code 0.
        """
        with mock_list(config) as lister:
            lister.list_epics.return_value = []
            result = runner.invoke(app, ["epics", "list", "my-project"])

        assert result.exit_code == 0
        assert result.output == ""

    def test_unknown_slug_exits_nonzero(self, config):
        """Setup: resolve_project raises ResolveError.
        Expectations: exit code 1.
        """
        with mock_list(config, resolve_error=ResolveError("Project 'bad-slug' not found")):
            result = runner.invoke(app, ["epics", "list", "bad-slug"])

        assert result.exit_code == 1

    def test_unknown_slug_prints_error(self, config):
        """Setup: resolve_project raises ResolveError with message.
        Expectations: exact error message in output.
        """
        with mock_list(config, resolve_error=ResolveError("Project 'bad-slug' not found")):
            result = runner.invoke(app, ["epics", "list", "bad-slug"])

        assert result.output == "Project 'bad-slug' not found\n"

    def test_resolve_project_called_with_slug(self, config):
        """Setup: slug passed as argument.
        Expectations: resolve_project called with that slug.
        """
        with mock_list(config) as lister, \
             patch("taigun.cli.Resolver") as mock_resolver_cls:
            mock_resolver_cls.return_value.resolve_project.return_value = 1
            lister.list_epics.return_value = []
            runner.invoke(app, ["epics", "list", "my-project"])

        mock_resolver_cls.return_value.resolve_project.assert_called_once_with("my-project")


class TestStatusesList:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    @pytest.fixture
    def sample_statuses(self):
        return {
            "story": [("New", False), ("In Progress", False), ("Done", True)],
            "task": [("New", False), ("Done", True)],
            "issue": [("New", False), ("Done", True)],
            "epic": [("New", False), ("Done", True)],
        }

    def test_output_format(self, config, sample_statuses):
        """Setup: statuses for all four types.
        Expectations: exact grouped output with headers and indented status names.
        """
        with mock_list(config) as lister:
            lister.list_statuses.return_value = sample_statuses
            result = runner.invoke(app, ["statuses", "list", "my-project"])

        expected = (
            "story:\n"
            "  New\n"
            "  In Progress\n"
            "  Done  [closed]\n"
            "task:\n"
            "  New\n"
            "  Done  [closed]\n"
            "issue:\n"
            "  New\n"
            "  Done  [closed]\n"
            "epic:\n"
            "  New\n"
            "  Done  [closed]\n"
        )
        assert result.exit_code == 0
        assert result.output == expected

    def test_unknown_slug_exits_nonzero(self, config):
        """Setup: resolve_project raises ResolveError.
        Expectations: exit code 1.
        """
        with mock_list(config, resolve_error=ResolveError("Project 'bad-slug' not found")):
            result = runner.invoke(app, ["statuses", "list", "bad-slug"])

        assert result.exit_code == 1

    def test_unknown_slug_prints_error(self, config):
        """Setup: resolve_project raises ResolveError with message.
        Expectations: exact error message in output.
        """
        with mock_list(config, resolve_error=ResolveError("Project 'bad-slug' not found")):
            result = runner.invoke(app, ["statuses", "list", "bad-slug"])

        assert result.output == "Project 'bad-slug' not found\n"
