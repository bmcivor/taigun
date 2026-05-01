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

TICKET_TYPES = ["story", "issue", "task", "epic"]


def write_ticket(tmp_path: Path, name: str, ticket_type: str, subject: str = "The subject") -> Path:
    """Write a minimal valid markdown ticket file and return its path."""
    content = f"---\ntype: {ticket_type}\nproject: my-project\n---\n\n## {subject}\n"
    path = tmp_path / name
    path.write_text(content)
    return path


def make_config(tmp_path: Path) -> ConfigManager:
    config = ConfigManager(path=tmp_path / "config.toml")
    config.save(PROFILE, name=None)
    return config


@contextmanager
def mock_push(config: ConfigManager, write_return=42, write_error=None):
    """Patch only the database layer. Yields (mock_writer, mock_cm)."""
    mock_writer = MagicMock()
    if write_error:
        mock_writer.return_value.write.side_effect = write_error
    else:
        mock_writer.return_value.write.return_value = write_return

    with patch("taigun.cli.ConfigManager", return_value=config), \
         patch("taigun.cli.ConnectionManager") as mock_cm, \
         patch("taigun.cli.Resolver"), \
         patch("taigun.cli._WRITERS", {t: mock_writer for t in TICKET_TYPES}):

        mock_cm.return_value.connect.return_value.__enter__.return_value = MagicMock()
        mock_cm.return_value.connect.return_value.__exit__.return_value = False

        yield mock_writer, mock_cm


class TestPushOutputFormat:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    @pytest.fixture
    def path(self, tmp_path):
        return write_ticket(tmp_path, "ticket.md", "story", subject="The subject")

    @pytest.mark.parametrize("ticket_type", TICKET_TYPES)
    def test_success_line_format(self, tmp_path, config, ticket_type):
        """Setup: single file; write returns ref 42.
        Expectations: output line is '✓ #42 <type>: "<subject>"'.
        """
        path = write_ticket(tmp_path, "ticket.md", ticket_type, subject="The subject")
        with mock_push(config):
            result = runner.invoke(app, ["push", str(path)])

        assert result.exit_code == 0
        assert f'✓ #42 {ticket_type}: "The subject"' in result.output

    @pytest.mark.parametrize("ticket_type", TICKET_TYPES)
    def test_dry_run_line_format(self, tmp_path, config, ticket_type):
        """Setup: --dry-run; single valid ticket file.
        Expectations: output line is '~ <type>: "<subject>"' with no ref.
        """
        path = write_ticket(tmp_path, "ticket.md", ticket_type, subject="The subject")
        with mock_push(config):
            result = runner.invoke(app, ["push", "--dry-run", str(path)])

        assert result.exit_code == 0
        assert f'~ {ticket_type}: "The subject"' in result.output
        assert "✓" not in result.output


class TestPushMultipleFiles:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    @pytest.fixture
    def paths(self, tmp_path):
        return [
            write_ticket(tmp_path, "a.md", "story", subject="First"),
            write_ticket(tmp_path, "b.md", "story", subject="Second"),
        ]

    def test_all_files_produce_output_lines(self, config, paths):
        """Setup: two valid ticket files.
        Expectations: two success lines in output; exit code 0.
        """
        with mock_push(config):
            result = runner.invoke(app, ["push"] + [str(p) for p in paths])

        assert result.exit_code == 0
        assert result.output.count("✓") == 2


class TestPushExitCodes:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    @pytest.fixture
    def path(self, tmp_path):
        return write_ticket(tmp_path, "ticket.md", "story")

    def test_exit_zero_all_success(self, config, path):
        """Setup: single valid file; write succeeds.
        Expectations: exit code 0.
        """
        with mock_push(config):
            result = runner.invoke(app, ["push", str(path)])

        assert result.exit_code == 0

    def test_exit_one_on_parse_error(self, tmp_path, config):
        """Setup: file with invalid frontmatter (missing project).
        Expectations: exit code 1.
        """
        bad = tmp_path / "bad.md"
        bad.write_text("---\ntype: story\n---\n\n## Title\n")

        with mock_push(config):
            result = runner.invoke(app, ["push", str(bad)])

        assert result.exit_code == 1

    def test_exit_one_on_write_error(self, config, path):
        """Setup: valid file; write raises ResolveError.
        Expectations: exit code 1.
        """
        with mock_push(config, write_error=ResolveError("project not found")):
            result = runner.invoke(app, ["push", str(path)])

        assert result.exit_code == 1

    def test_exit_one_when_only_some_fail(self, tmp_path, config):
        """Setup: two files; first has invalid frontmatter, second is valid.
        Expectations: exit code 1.
        """
        bad = tmp_path / "bad.md"
        bad.write_text("---\ntype: story\n---\n\n## Title\n")
        good = write_ticket(tmp_path, "good.md", "story")

        with mock_push(config):
            result = runner.invoke(app, ["push", str(bad), str(good)])

        assert result.exit_code == 1


class TestPushFailureContinuation:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    def test_remaining_files_pushed_after_parse_failure(self, tmp_path, config):
        """Setup: two files; first has invalid frontmatter; second is valid.
        Expectations: second file is still pushed; success line in output.
        """
        bad = tmp_path / "bad.md"
        bad.write_text("---\ntype: story\n---\n\n## Title\n")
        good = write_ticket(tmp_path, "good.md", "story", subject="Good one")

        with mock_push(config):
            result = runner.invoke(app, ["push", str(bad), str(good)])

        assert '✓ #42 story: "Good one"' in result.output

    def test_remaining_files_pushed_after_write_failure(self, tmp_path, config):
        """Setup: two files; write fails on first; second succeeds.
        Expectations: second file is still pushed; success line in output.
        """
        path_a = write_ticket(tmp_path, "a.md", "story", subject="First")
        path_b = write_ticket(tmp_path, "b.md", "story", subject="Second")

        mock_writer = MagicMock()
        mock_writer.return_value.write.side_effect = [ResolveError("not found"), 42]

        with patch("taigun.cli.ConfigManager", return_value=config), \
             patch("taigun.cli.ConnectionManager") as mock_cm, \
             patch("taigun.cli.Resolver"), \
             patch("taigun.cli._WRITERS", {t: mock_writer for t in TICKET_TYPES}):

            mock_cm.return_value.connect.return_value.__enter__.return_value = MagicMock()
            mock_cm.return_value.connect.return_value.__exit__.return_value = False

            result = runner.invoke(app, ["push", str(path_a), str(path_b)])

        assert '✓ #42 story: "Second"' in result.output

    def test_error_message_includes_filename(self, tmp_path, config):
        """Setup: file has invalid frontmatter.
        Expectations: error output includes the filename.
        """
        bad = tmp_path / "broken.md"
        bad.write_text("---\ntype: story\n---\n\n## Title\n")

        with mock_push(config):
            result = runner.invoke(app, ["push", str(bad)])

        assert "broken.md" in result.output


class TestPushDryRun:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    @pytest.fixture
    def path(self, tmp_path):
        return write_ticket(tmp_path, "ticket.md", "story")

    def test_connect_called_with_dry_run_true(self, config, path):
        """Setup: --dry-run flag.
        Expectations: connect() called with dry_run=True.
        """
        with mock_push(config) as (_, mock_cm):
            runner.invoke(app, ["push", "--dry-run", str(path)])

        mock_cm.return_value.connect.assert_called_once_with(dry_run=True)

    def test_normal_connect_called_without_dry_run(self, config, path):
        """Setup: no --dry-run flag.
        Expectations: connect() called with dry_run=False.
        """
        with mock_push(config) as (_, mock_cm):
            runner.invoke(app, ["push", str(path)])

        mock_cm.return_value.connect.assert_called_once_with(dry_run=False)

    def test_write_still_called_in_dry_run(self, config, path):
        """Setup: --dry-run; single story file.
        Expectations: writer.write() is still called (FKs resolved).
        """
        with mock_push(config) as (mock_writer, _):
            runner.invoke(app, ["push", "--dry-run", str(path)])

        mock_writer.return_value.write.assert_called_once()


class TestPushProfile:
    @pytest.fixture
    def config(self, tmp_path):
        config = make_config(tmp_path)
        work_profile = Profile("workhost", 5432, "taiga", "taiga", "secret", "workuser")
        config.save(work_profile, name="work")
        return config

    @pytest.fixture
    def path(self, tmp_path):
        return write_ticket(tmp_path, "ticket.md", "story")

    @pytest.mark.parametrize("extra_args,expected_user", [
        ([], "admin"),
        (["--profile", "work"], "workuser"),
    ])
    def test_profile_flag_loads_correct_profile(self, config, path, extra_args, expected_user):
        """Setup: --profile flag present or absent; matching profile exists in config.
        Expectations: correct profile's acting_user is used.
        """
        with patch("taigun.cli.ConfigManager", return_value=config), \
             patch("taigun.cli.ConnectionManager") as mock_cm, \
             patch("taigun.cli.Resolver"), \
             patch("taigun.cli._WRITERS", {t: MagicMock() for t in TICKET_TYPES}) as mock_writers:

            mock_cm.return_value.connect.return_value.__enter__.return_value = MagicMock()
            mock_cm.return_value.connect.return_value.__exit__.return_value = False
            for w in mock_writers.values():
                w.return_value.write.return_value = 42

            runner.invoke(app, ["push"] + extra_args + [str(path)])

        used_profile = mock_cm.call_args.args[0]
        assert used_profile.acting_user == expected_user
