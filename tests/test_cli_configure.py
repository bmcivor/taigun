from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from taigun.cli import app
from taigun.config import ConfigManager, Profile

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

EXISTING_PROFILE = Profile("oldhost", 5432, "taiga", "taiga", "secret", "admin")


def make_inputs(*parts: list[str]) -> str:
    return "\n".join(line for part in parts for line in part)


def make_config(tmp_path: Path) -> ConfigManager:
    return ConfigManager(path=tmp_path / "config.toml")


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
def patch_config(config: ConfigManager):
    with patch("taigun.cli.ConfigManager", return_value=config):
        yield config


class TestConfigureHappyPath:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    @pytest.fixture
    def inputs(self):
        return make_inputs([PROFILE_PROMPT_DEFAULT], VALID_INPUTS)

    @pytest.mark.parametrize("profile_flag,profile_input,expected_profile_name", [
        (["--profile", "work"], [], "work"),
        ([], [PROFILE_PROMPT_DEFAULT], None),
        ([], ["staging"], "staging"),
    ])
    def test_saves_profile(self, config, profile_flag, profile_input, expected_profile_name):
        """Setup: valid inputs, connection succeeds, no existing profile.
        Expectations: profile loadable after save; exit code 0.
        """
        inputs = make_inputs(profile_input, VALID_INPUTS)
        with patch_config(config), mock_connection_ok():
            result = runner.invoke(app, ["configure"] + profile_flag, input=inputs)

        assert result.exit_code == 0
        loaded = config.load(expected_profile_name)
        assert loaded.host == "myhost"
        assert loaded.acting_user == "admin"

    def test_prints_success(self, config, inputs):
        """Setup: valid inputs, connection succeeds.
        Expectations: output contains success message.
        """
        with patch_config(config), mock_connection_ok():
            result = runner.invoke(app, ["configure"], input=inputs)

        assert "saved" in result.output

    def test_profile_saved_with_correct_fields(self, config):
        """Setup: specific input values.
        Expectations: loaded profile has all fields set correctly.
        """
        inputs = make_inputs([PROFILE_PROMPT_DEFAULT], [
            "db.example.com", "5433", "mydb", "myuser", "mypass", "myactor"
        ])
        with patch_config(config), mock_connection_ok():
            runner.invoke(app, ["configure"], input=inputs)

        profile = config.load(None)
        assert profile.host == "db.example.com"
        assert profile.port == 5433
        assert profile.database == "mydb"
        assert profile.username == "myuser"
        assert profile.password == "mypass"
        assert profile.acting_user == "myactor"


class TestConfigureConnectionFailure:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    @pytest.fixture
    def inputs(self):
        return make_inputs([PROFILE_PROMPT_DEFAULT], VALID_INPUTS)

    def test_exits_nonzero_on_failure(self, config, inputs):
        """Setup: connection fails.
        Expectations: exit code is 1.
        """
        with patch_config(config), mock_connection_fail():
            result = runner.invoke(app, ["configure"], input=inputs)

        assert result.exit_code == 1

    def test_prints_error_on_failure(self, config, inputs):
        """Setup: connection fails with a specific message.
        Expectations: error message appears in output.
        """
        with patch_config(config), mock_connection_fail("Could not connect to database: timeout"):
            result = runner.invoke(app, ["configure"], input=inputs)

        assert "Could not connect to database: timeout" in result.output

    def test_does_not_save_on_failure(self, config, inputs):
        """Setup: connection fails.
        Expectations: config file is not written.
        """
        with patch_config(config), mock_connection_fail():
            runner.invoke(app, ["configure"], input=inputs)

        assert not config._path.exists()


class TestConfigureExistingProfile:
    @pytest.fixture
    def config(self, tmp_path):
        config = make_config(tmp_path)
        config.save(EXISTING_PROFILE, name=None)
        return config

    @pytest.mark.parametrize("confirm_input,expect_saved", [
        ("y", True),
        ("n", False),
    ])
    def test_overwrite_prompt(self, config, confirm_input, expect_saved):
        """Setup: profile already exists; user confirms or declines overwrite.
        Expectations: profile saved or not; exit code 0 either way.
        """
        inputs = make_inputs(
            [PROFILE_PROMPT_DEFAULT],
            [confirm_input] + (VALID_INPUTS if confirm_input == "y" else []),
        )
        with patch_config(config), mock_connection_ok():
            result = runner.invoke(app, ["configure"], input=inputs)

        assert result.exit_code == 0
        loaded = config.load(None)
        assert loaded.host == ("myhost" if expect_saved else "oldhost")

    def test_profile_flag_still_checks_existing(self, tmp_path, config):
        """Setup: --profile work passed; profile 'work' already exists; user declines.
        Expectations: existing profile unchanged.
        """
        config.save(EXISTING_PROFILE, name="work")
        with patch_config(config), mock_connection_ok():
            result = runner.invoke(app, ["configure", "--profile", "work"], input="n\n")

        assert result.exit_code == 0
        assert config.load("work").host == "oldhost"
