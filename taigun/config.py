import tomllib
import tomli_w
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


CONFIG_PATH = Path.home() / ".config" / "taigun" / "config.toml"

REQUIRED_FIELDS = ["host", "port", "database", "username", "password", "acting_user"]


@dataclass
class Profile:
    host: str
    port: int
    database: str
    username: str
    password: str
    acting_user: str


def load_config(profile: Optional[str] = None) -> Profile:
    """Load a connection profile from the config file.

    Args:
        profile: Named profile to load. Loads the default profile if None.

    Returns:
        A populated Profile dataclass.

    Raises:
        SystemExit: If the config file is missing, the profile does not exist,
            or required fields are absent.
    """
    if not CONFIG_PATH.exists():
        raise SystemExit(
            f"No config file found at {CONFIG_PATH}. Run 'taigun configure' to set one up."
        )

    with CONFIG_PATH.open("rb") as f:
        data = tomllib.load(f)

    if profile is None:
        section = data.get("default")
        section_name = "default"
    else:
        section = data.get("profiles", {}).get(profile)
        section_name = f"profiles.{profile}"

    if section is None:
        raise SystemExit(
            f"Profile '{section_name}' not found in {CONFIG_PATH}."
        )

    missing = [field for field in REQUIRED_FIELDS if field not in section]
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


def save_config(profile: Profile, name: Optional[str] = None) -> None:
    """Write a profile to the config file.

    Args:
        profile: The profile to save.
        name: Profile name. Saves as the default profile if None.
    """
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    data: dict = {}
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("rb") as f:
            data = tomllib.load(f)

    section = asdict(profile)

    if name is None:
        data["default"] = section
    else:
        data.setdefault("profiles", {})[name] = section

    with CONFIG_PATH.open("wb") as f:
        tomli_w.dump(data, f)
