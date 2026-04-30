from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from taigun.cli import app

runner = CliRunner()

VALID_INPUTS = [
    "myhost",   # host
    "5432",     # port
    "taiga",    # database
    "taiga",    # username
    "secret",   # password
    "admin",    # acting_user
]

PROFILE_PROMPT_DEFAULT = "default"


def make_inputs(*parts: list[str]) -> str:
    return "\n".join(line for part in parts for line in part)


@contextmanager
def mock_connection_ok():
    with patch("taigun.cli.ConnectionManager") as mock_cm:
        mock_cm.return_value.connect.return_value = MagicMock(
            __enter__=lambda s, *a: s,
            __exit__=lambda s, *a: False,
        )
        yield mock_cm


@contextmanager
def mock_connection_fail(message: str = "Could not connect to database: timeout"):
    with patch("taigun.cli.ConnectionManager") as mock_cm:
        mock_cm.return_value.connect.side_effect = SystemExit(message)
        yield mock_cm


@contextmanager
def mock_no_existing_profile():
    with patch("taigun.cli.ConfigManager") as mock_cfg:
        mock_cfg.return_value.load.side_effect = SystemExit("not found")
        yield mock_cfg


@contextmanager
def mock_existing_profile():
    with patch("taigun.cli.ConfigManager") as mock_cfg:
        mock_cfg.return_value.load.return_value = MagicMock()
        yield mock_cfg


class TestConfigureHappyPath:
    @pytest.mark.parametrize("profile_flag,profile_input,expected_save_name", [
        # --profile flag skips profile name prompt
        (["--profile", "work"], [], "work"),
        # no flag: accept default profile name
        ([], [PROFILE_PROMPT_DEFAULT], None),
        # no flag: enter a custom profile name
        ([], ["staging"], "staging"),
    ])
    def test_saves_profile(self, profile_flag, profile_input, expected_save_name):
        """Setup: valid inputs, connection succeeds, no existing profile.
        Expectations: save called with correct profile name; exit code 0.
        """
        inputs = make_inputs(profile_input, VALID_INPUTS)
        with mock_no_existing_profile() as mock_cfg, mock_connection_ok():
            result = runner.invoke(app, ["configure"] + profile_flag, input=inputs)

        assert result.exit_code == 0
        mock_cfg.return_value.save.assert_called_once()
        call_args = mock_cfg.return_value.save.call_args
        name_arg = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get("name")
        assert name_arg == expected_save_name

    def test_prints_success(self):
        """Setup: valid inputs, connection succeeds.
        Expectations: output contains success message.
        """
        inputs = make_inputs([PROFILE_PROMPT_DEFAULT], VALID_INPUTS)
        with mock_no_existing_profile(), mock_connection_ok():
            result = runner.invoke(app, ["configure"], input=inputs)

        assert "saved" in result.output

    def test_profile_saved_with_correct_fields(self):
        """Setup: specific input values.
        Expectations: Profile passed to save has all fields set correctly.
        """
        inputs = make_inputs([PROFILE_PROMPT_DEFAULT], [
            "db.example.com", "5433", "mydb", "myuser", "mypass", "myactor"
        ])
        with mock_no_existing_profile() as mock_cfg, mock_connection_ok():
            runner.invoke(app, ["configure"], input=inputs)

        profile = mock_cfg.return_value.save.call_args.args[0]
        assert profile.host == "db.example.com"
        assert profile.port == 5433
        assert profile.database == "mydb"
        assert profile.username == "myuser"
        assert profile.password == "mypass"
        assert profile.acting_user == "myactor"


class TestConfigureConnectionFailure:
    def test_exits_nonzero_on_failure(self):
        """Setup: connection fails.
        Expectations: exit code is 1.
        """
        inputs = make_inputs([PROFILE_PROMPT_DEFAULT], VALID_INPUTS)
        with mock_no_existing_profile(), mock_connection_fail():
            result = runner.invoke(app, ["configure"], input=inputs)

        assert result.exit_code == 1

    def test_prints_error_on_failure(self):
        """Setup: connection fails with a specific message.
        Expectations: error message appears in output.
        """
        inputs = make_inputs([PROFILE_PROMPT_DEFAULT], VALID_INPUTS)
        with mock_no_existing_profile(), mock_connection_fail("Could not connect to database: timeout"):
            result = runner.invoke(app, ["configure"], input=inputs)

        assert "Could not connect to database: timeout" in result.output

    def test_does_not_save_on_failure(self):
        """Setup: connection fails.
        Expectations: save is never called.
        """
        inputs = make_inputs([PROFILE_PROMPT_DEFAULT], VALID_INPUTS)
        with mock_no_existing_profile() as mock_cfg, mock_connection_fail():
            runner.invoke(app, ["configure"], input=inputs)

        mock_cfg.return_value.save.assert_not_called()


class TestConfigureExistingProfile:
    @pytest.mark.parametrize("confirm_input,expect_save,expect_exit_zero", [
        ("y", True, True),   # confirm overwrite → save
        ("n", False, True),  # decline overwrite → abort cleanly
    ])
    def test_overwrite_prompt(self, confirm_input, expect_save, expect_exit_zero):
        """Setup: profile already exists; user confirms or declines overwrite.
        Expectations: save called/not called; exit code correct.
        """
        inputs = make_inputs(
            [PROFILE_PROMPT_DEFAULT],
            [confirm_input] + (VALID_INPUTS if confirm_input == "y" else []),
        )
        with mock_existing_profile() as mock_cfg, mock_connection_ok():
            result = runner.invoke(app, ["configure"], input=inputs)

        assert result.exit_code == 0
        if expect_save:
            mock_cfg.return_value.save.assert_called_once()
        else:
            mock_cfg.return_value.save.assert_not_called()

    def test_profile_flag_still_checks_existing(self):
        """Setup: --profile work passed; profile 'work' already exists; user declines.
        Expectations: save not called.
        """
        with mock_existing_profile() as mock_cfg, mock_connection_ok():
            result = runner.invoke(app, ["configure", "--profile", "work"], input="n\n")

        assert result.exit_code == 0
        mock_cfg.return_value.save.assert_not_called()
