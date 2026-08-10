from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from taigun.cli import app
from taigun.config import ConfigManager, Profile

runner = CliRunner()


def make_config(tmp_path: Path) -> ConfigManager:
    return ConfigManager(path=tmp_path / "config.toml")


def make_inputs(*parts):
    return "\n".join(line for part in parts for line in part)


def valid_inputs_for(profile: Profile) -> list[str]:
    """Build the stdin sequence for the configure prompts using a real Profile."""
    return [
        profile.host,
        str(profile.port),
        profile.database,
        profile.username,
        profile.password,
        profile.acting_user,
    ]


def bad_host_inputs() -> list[str]:
    """Inputs that point at a host that will fail to connect."""
    return [
        "nonexistent-host-xyz",
        "5432",
        "taiga",
        "taiga",
        "taiga",
        "admin",
    ]


@contextmanager
def patch_config(config: ConfigManager):
    with patch("taigun.cli.ConfigManager", return_value=config):
        yield config


class TestConfigureHappyPath:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    def test_saves_default_profile_against_real_db(self, config, test_db_profile):
        """Setup: valid prompts pointing at test-db; no existing profile.
        Expectations: profile is saved as the default, exit 0.
        """
        inputs = make_inputs(["default"], valid_inputs_for(test_db_profile))

        with patch_config(config):
            result = runner.invoke(app, ["configure"], input=inputs)

        assert result.exit_code == 0
        loaded = config.load(None)
        assert loaded.host == test_db_profile.host
        assert loaded.port == test_db_profile.port

    def test_saves_named_profile_via_flag(self, config, test_db_profile):
        """Setup: --profile work flag, valid inputs.
        Expectations: profile saved under name 'work'.
        """
        inputs = make_inputs(valid_inputs_for(test_db_profile))

        with patch_config(config):
            result = runner.invoke(
                app, ["configure", "--profile", "work"], input=inputs
            )

        assert result.exit_code == 0
        loaded = config.load("work")
        assert loaded.host == test_db_profile.host

    def test_prints_success_message(self, config, test_db_profile):
        """Setup: successful configure.
        Expectations: final output line is exactly "Profile 'default' saved."
        """
        inputs = make_inputs(["default"], valid_inputs_for(test_db_profile))

        with patch_config(config):
            result = runner.invoke(app, ["configure"], input=inputs)

        assert result.output.splitlines()[-1] == "Profile 'default' saved."


class TestConfigureConnectionFailure:
    @pytest.fixture
    def config(self, tmp_path):
        return make_config(tmp_path)

    def test_exits_nonzero_when_host_unreachable(self, config):
        """Setup: host that cannot be resolved/reached.
        Expectations: exit code 1.
        """
        inputs = make_inputs(["default"], bad_host_inputs())

        with patch_config(config):
            result = runner.invoke(app, ["configure"], input=inputs)

        assert result.exit_code == 1

    def test_does_not_save_when_host_unreachable(self, config):
        """Setup: host that cannot be resolved/reached.
        Expectations: config file is not written.
        """
        inputs = make_inputs(["default"], bad_host_inputs())

        with patch_config(config):
            runner.invoke(app, ["configure"], input=inputs)

        assert not config._path.exists()


class TestConfigureExistingProfile:
    @pytest.fixture
    def config(self, tmp_path, test_db_profile):
        config = make_config(tmp_path)
        existing = Profile("oldhost", 5432, "taiga", "taiga", "secret", "admin")
        config.save(existing, name=None)
        return config

    def test_declines_overwrite_leaves_existing(self, config):
        """Setup: profile already exists; user answers 'n' to overwrite prompt.
        Expectations: existing profile unchanged; exit 0.
        """
        inputs = make_inputs(["default"], ["n"])

        with patch_config(config):
            result = runner.invoke(app, ["configure"], input=inputs)

        assert result.exit_code == 0
        assert config.load(None).host == "oldhost"

    def test_accepts_overwrite_replaces_existing(self, config, test_db_profile):
        """Setup: profile already exists; user answers 'y' and re-enters real values.
        Expectations: profile replaced with new values; exit 0.
        """
        inputs = make_inputs(["default"], ["y"], valid_inputs_for(test_db_profile))

        with patch_config(config):
            result = runner.invoke(app, ["configure"], input=inputs)

        assert result.exit_code == 0
        assert config.load(None).host == test_db_profile.host
