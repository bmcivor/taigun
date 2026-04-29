import pytest
import tomli_w
from pathlib import Path

from taigun.config import ConfigManager, Profile


VALID_PROFILE = {
    "host": "localhost",
    "port": 5432,
    "database": "taiga",
    "username": "taiga",
    "password": "secret",
    "acting_user": "admin",
}


@pytest.fixture
def config_path(tmp_path) -> Path:
    return tmp_path / ".config" / "taigun" / "config.toml"


@pytest.fixture
def manager(config_path) -> ConfigManager:
    return ConfigManager(path=config_path)


def write_config(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        tomli_w.dump(data, f)


class TestConfigManagerLoad:
    def test_missing_file_raises(self, manager):
        """Setup: no config file exists.
        Expectations: SystemExit with message directing user to taigun configure.
        """
        with pytest.raises(SystemExit, match="taigun configure"):
            manager.load()

    def test_loads_default_profile(self, manager, config_path):
        """Setup: config file with a default profile.
        Expectations: returns a Profile with correct field values.
        """
        write_config(config_path, {"default": VALID_PROFILE})
        profile = manager.load()

        assert profile.host == "localhost"
        assert profile.port == 5432
        assert profile.database == "taiga"
        assert profile.username == "taiga"
        assert profile.password == "secret"
        assert profile.acting_user == "admin"

    def test_loads_named_profile(self, manager, config_path):
        """Setup: config file with a named profile.
        Expectations: returns the correct profile when name is specified.
        """
        write_config(config_path, {"profiles": {"lab": VALID_PROFILE}})
        profile = manager.load(profile="lab")

        assert profile.host == "localhost"

    def test_missing_default_profile_raises(self, manager, config_path):
        """Setup: config file exists but has no default section.
        Expectations: SystemExit naming the missing profile.
        """
        write_config(config_path, {"profiles": {"lab": VALID_PROFILE}})
        with pytest.raises(SystemExit, match="default"):
            manager.load()

    def test_missing_named_profile_raises(self, manager, config_path):
        """Setup: config file exists but the requested profile is absent.
        Expectations: SystemExit naming the missing profile.
        """
        write_config(config_path, {"default": VALID_PROFILE})
        with pytest.raises(SystemExit, match="other"):
            manager.load(profile="other")

    def test_missing_required_field_raises(self, manager, config_path):
        """Setup: default profile is missing the password field.
        Expectations: SystemExit naming the missing field.
        """
        incomplete = {k: v for k, v in VALID_PROFILE.items() if k != "password"}
        write_config(config_path, {"default": incomplete})
        with pytest.raises(SystemExit, match="password"):
            manager.load()

    def test_port_coerced_to_int(self, manager, config_path):
        """Setup: port value stored as string in config.
        Expectations: Profile.port is an int.
        """
        profile_with_str_port = {**VALID_PROFILE, "port": "5432"}
        write_config(config_path, {"default": profile_with_str_port})
        profile = manager.load()

        assert isinstance(profile.port, int)


class TestConfigManagerSave:
    def test_saves_default_profile(self, manager):
        """Setup: no existing config.
        Expectations: saves profile under [default] and can be loaded back.
        """
        profile = Profile(**VALID_PROFILE)
        manager.save(profile)

        assert manager.load() == profile

    def test_saves_named_profile(self, manager):
        """Setup: no existing config.
        Expectations: saves profile under [profiles.lab] and can be loaded back.
        """
        profile = Profile(**VALID_PROFILE)
        manager.save(profile, name="lab")

        assert manager.load(profile="lab") == profile

    def test_creates_config_directory(self, manager, config_path):
        """Setup: config directory does not exist.
        Expectations: directory and file are created on save.
        """
        assert not config_path.exists()
        manager.save(Profile(**VALID_PROFILE))

        assert config_path.exists()

    def test_preserves_existing_profiles(self, manager):
        """Setup: config already has a default profile.
        Expectations: saving a named profile does not overwrite the default.
        """
        profile = Profile(**VALID_PROFILE)
        manager.save(profile)
        manager.save(Profile(**{**VALID_PROFILE, "host": "otherhost"}), name="other")

        assert manager.load().host == "localhost"
        assert manager.load(profile="other").host == "otherhost"
