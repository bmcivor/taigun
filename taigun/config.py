import tomllib
import tomli_w
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Profile:
    host: str
    port: int
    database: str
    username: str
    password: str
    acting_user: str


class ConfigManager:
    """Reads and writes taigun connection profiles from a TOML config file.

    Supports a ``[default]`` profile and named profiles under
    ``[profiles.<name>]``.
    """

    DEFAULT_PATH = Path.home() / ".config" / "taigun" / "config.toml"
    REQUIRED_FIELDS = ["host", "port", "database", "username", "password", "acting_user"]

    def __init__(self, path: Path = DEFAULT_PATH) -> None:
        self._path = path

    def load(self, profile: Optional[str] = None) -> Profile:
        """Load a connection profile from the config file.

        Args:
            profile: Named profile to load. Loads the default profile if None.

        Returns:
            A populated Profile dataclass.

        Raises:
            SystemExit: If the config file is missing, the profile does not exist,
                or required fields are absent.
        """
        if not self._path.exists():
            raise SystemExit(
                f"No config file found at {self._path}. Run 'taigun configure' to set one up."
            )

        with self._path.open("rb") as f:
            data = tomllib.load(f)

        if profile is None:
            section = data.get("default")
            section_name = "default"
        else:
            section = data.get("profiles", {}).get(profile)
            section_name = f"profiles.{profile}"

        if section is None:
            raise SystemExit(f"Profile '{section_name}' not found in {self._path}.")

        missing = [field for field in self.REQUIRED_FIELDS if field not in section]
        if missing:
            raise SystemExit(
                f"Profile '{section_name}' is missing required fields: {', '.join(missing)}"
            )

        return Profile(
            host=section["host"],
            port=int(section["port"]),
            database=section["database"],
            username=section["username"],
            password=section["password"],
            acting_user=section["acting_user"],
        )

    def save(self, profile: Profile, name: Optional[str] = None) -> None:
        """Write a profile to the config file.

        Args:
            profile: The profile to save.
            name: Profile name. Saves as the default profile if None.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)

        data: dict = {}
        if self._path.exists():
            with self._path.open("rb") as f:
                data = tomllib.load(f)

        section = asdict(profile)

        if name is None:
            data["default"] = section
        else:
            data.setdefault("profiles", {})[name] = section

        with self._path.open("wb") as f:
            tomli_w.dump(data, f)
