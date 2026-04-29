import pytest
import tomli_w
from pathlib import Path

import taigun.config as config_module
from taigun.config import load_config, save_config, Profile


VALID_PROFILE = {
    "host": "localhost",
    "port": 5432,
    "database": "taiga",
    "username": "taiga",
    "password": "secret",
    "acting_user": "admin",
}


@pytest.fixture(autouse=True)
def patch_config_path(tmp_path, monkeypatch):
    """Redirect CONFIG_PATH to a temp directory for all tests."""
    fake_path = tmp_path / ".config" / "taigun" / "config.toml"
    monkeypatch.setattr(config_module, "CONFIG_PATH", fake_path)
    return fake_path


def write_config(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        tomli_w.dump(data, f)


class TestLoadConfig:
    def test_missing_file_raises(self):
        """Setup: no config file exists.
        Expectations: SystemExit with message directing user to taigun configure.
        """
        with pytest.raises(SystemExit, match="taigun configure"):
            load_config()

    def test_loads_default_profile(self, patch_config_path):
        """Setup: config file with a default profile.
        Expectations: returns a Profile with correct field values.
        """
        write_config(patch_config_path, {"default": VALID_PROFILE})
        profile = load_config()
        assert profile.host == "localhost"
        assert profile.port == 5432
        assert profile.database == "taiga"
        assert profile.username == "taiga"
        assert profile.password == "secret"
        assert profile.acting_user == "admin"

    def test_loads_named_profile(self, patch_config_path):
        """Setup: config file with a named profile.
        Expectations: returns the correct profile when name is specified.
        """
        write_config(patch_config_path, {"profiles": {"lab": VALID_PROFILE}})
        profile = load_config(profile="lab")
        assert profile.host == "localhost"

    def test_missing_default_profile_raises(self, patch_config_path):
        """Setup: config file exists but has no default section.
        Expectations: SystemExit naming the missing profile.
        """
        write_config(patch_config_path, {"profiles": {"lab": VALID_PROFILE}})
        with pytest.raises(SystemExit, match="default"):
            load_config()

    def test_missing_named_profile_raises(self, patch_config_path):
        """Setup: config file exists but the requested profile is absent.
        Expectations: SystemExit naming the missing profile.
        """
        write_config(patch_config_path, {"default": VALID_PROFILE})
        with pytest.raises(SystemExit, match="other"):
            load_config(profile="other")

    def test_missing_required_field_raises(self, patch_config_path):
        """Setup: default profile is missing the password field.
        Expectations: SystemExit naming the missing field.
        """
        incomplete = {k: v for k, v in VALID_PROFILE.items() if k != "password"}
        write_config(patch_config_path, {"default": incomplete})
        with pytest.raises(SystemExit, match="password"):
            load_config()

    def test_port_coerced_to_int(self, patch_config_path):
        """Setup: port value stored as string in config.
        Expectations: Profile.port is an int.
        """
        profile_with_str_port = {**VALID_PROFILE, "port": "5432"}
        write_config(patch_config_path, {"default": profile_with_str_port})
        profile = load_config()
        assert isinstance(profile.port, int)


class TestSaveConfig:
    def test_saves_default_profile(self, patch_config_path):
        """Setup: no existing config.
        Expectations: saves profile under [default] and can be loaded back.
        """
        profile = Profile(**VALID_PROFILE)
        save_config(profile)
        loaded = load_config()
        assert loaded == profile

    def test_saves_named_profile(self, patch_config_path):
        """Setup: no existing config.
        Expectations: saves profile under [profiles.lab] and can be loaded back.
        """
        profile = Profile(**VALID_PROFILE)
        save_config(profile, name="lab")
        loaded = load_config(profile="lab")
        assert loaded == profile

    def test_creates_config_directory(self, patch_config_path):
        """Setup: config directory does not exist.
        Expectations: directory and file are created on save.
        """
        assert not patch_config_path.exists()
        save_config(Profile(**VALID_PROFILE))
        assert patch_config_path.exists()

    def test_preserves_existing_profiles(self, patch_config_path):
        """Setup: config already has a default profile.
        Expectations: saving a named profile does not overwrite the default.
        """
        profile = Profile(**VALID_PROFILE)
        save_config(profile)
        save_config(Profile(**{**VALID_PROFILE, "host": "otherhost"}), name="other")
        assert load_config().host == "localhost"
        assert load_config(profile="other").host == "otherhost"
