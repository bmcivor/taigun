"""Sidecar state file — maps source markdown files to the Taiga refs they
pushed as. See ADR-004 for the design.

Location: `.taigun/state.yaml` at the repo root (found by walking up from a
source file's directory, git-style).

Purpose: give push a way to detect "this file has already been pushed", so
future work (E9/034) can dispatch to an update path instead of always
inserting.
"""

import datetime
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml

from taigun.exceptions import TaigunError

SIDECAR_DIR_NAME = ".taigun"
SIDECAR_FILE_NAME = "state.yaml"
REPO_MARKER_NAME = ".git"


class StateError(TaigunError):
    """Raised when the sidecar can't be loaded (malformed YAML, duplicate
    entries, or missing required fields on an entry)."""


@dataclass
class StateEntry:
    """A single sidecar row.

    Fields mirror ADR-004's schema. `file_path` is stored relative to the
    sidecar's own directory so the file is portable across machines.
    """

    file_path: str
    project: str
    ref: int
    ticket_type: str
    last_pushed_at: str
    content_hash: str


class StateFile:
    """In-memory view of the sidecar, backed by a YAML file on disk.

    Typical flow:

        state = StateFile(sidecar_path)
        state.load()
        entry = state.find(source_file)
        # ... push work ...
        state.record(source_file, project, ref, ticket_type, content_hash)
        state.save()
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: Dict[str, StateEntry] = {}

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> None:
        """Read the sidecar from disk into memory.

        Missing file is fine — treated as empty. Malformed YAML, duplicate
        `file_path` values, or entries missing required fields all raise
        StateError. This is deliberately loud because the sidecar is
        committed to git and silent recovery from a broken one would let
        drift compound.
        """
        if not self._path.exists():
            self._entries = {}
            return

        try:
            raw = yaml.safe_load(self._path.read_text())
        except yaml.YAMLError as e:
            raise StateError(f"Sidecar YAML is malformed: {e}") from e

        if raw is None:
            self._entries = {}
            return

        if not isinstance(raw, dict) or "entries" not in raw:
            raise StateError("Sidecar must be a mapping with an 'entries' key")

        entries_list = raw["entries"] or []
        if not isinstance(entries_list, list):
            raise StateError("Sidecar 'entries' must be a list")

        loaded: dict[str, StateEntry] = {}
        for i, item in enumerate(entries_list):
            if not isinstance(item, dict):
                raise StateError(f"Sidecar entry #{i} is not a mapping")
            entry = self._build_entry(item, i)
            if entry.file_path in loaded:
                raise StateError(f"Duplicate file_path in sidecar: {entry.file_path!r}")
            loaded[entry.file_path] = entry

        self._entries = loaded

    def find(self, source_file: Path) -> Optional[StateEntry]:
        """Look up an entry by source-file path.

        The source_file is normalised to the sidecar's directory to match
        how paths are stored.
        """
        key = self._to_relative(source_file)
        return self._entries.get(key)

    def record(
        self,
        source_file: Path,
        project: str,
        ref: int,
        ticket_type: str,
        content_hash: str,
    ) -> None:
        """Add or replace an entry for the given source file.

        Does not write to disk — call save() when the whole push is done.
        """
        key = self._to_relative(source_file)
        self._entries[key] = StateEntry(
            file_path=key,
            project=project,
            ref=ref,
            ticket_type=ticket_type,
            last_pushed_at=_now_iso(),
            content_hash=content_hash,
        )

    def save(self) -> None:
        """Persist the in-memory entries to disk. Creates the .taigun/
        directory if it doesn't exist.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "entries": [
                {
                    "file_path": e.file_path,
                    "project": e.project,
                    "ref": e.ref,
                    "ticket_type": e.ticket_type,
                    "last_pushed_at": e.last_pushed_at,
                    "content_hash": e.content_hash,
                }
                for e in sorted(self._entries.values(), key=lambda x: x.file_path)
            ]
        }
        self._path.write_text(yaml.safe_dump(payload, sort_keys=False))

    def _to_relative(self, source_file: Path) -> str:
        """Normalise a source-file path to be relative to the repo root
        (the directory containing the ``.taigun/`` directory), using forward
        slashes so entries are portable across platforms.
        """
        repo_root = self._path.parent.parent.resolve()
        resolved = Path(source_file).resolve()
        try:
            rel = resolved.relative_to(repo_root)
        except ValueError:
            raise StateError(
                f"Source file {source_file!r} is not inside the sidecar's "
                f"repo root ({repo_root}); cannot compute relative path"
            )
        return rel.as_posix()

    def _build_entry(self, item: dict, index: int) -> StateEntry:
        required = (
            "file_path",
            "project",
            "ref",
            "ticket_type",
            "last_pushed_at",
            "content_hash",
        )
        missing = [f for f in required if f not in item]
        if missing:
            raise StateError(
                f"Sidecar entry #{index} missing fields: {', '.join(missing)}"
            )
        try:
            return StateEntry(
                file_path=str(item["file_path"]),
                project=str(item["project"]),
                ref=int(item["ref"]),
                ticket_type=str(item["ticket_type"]),
                last_pushed_at=str(item["last_pushed_at"]),
                content_hash=str(item["content_hash"]),
            )
        except (TypeError, ValueError) as e:
            raise StateError(f"Sidecar entry #{index} has an invalid field: {e}") from e


def locate_sidecar(start: Path) -> Path:
    """Find the sidecar file, walking up from a starting directory.

    Discovery order (git-style walk-up from ``start`` towards the filesystem
    root):

    1. Return the first `.taigun/state.yaml` that already exists.
    2. Otherwise, return `<repo-root>/.taigun/state.yaml` where ``repo-root``
       is the nearest ancestor containing a `.git/` directory. The sidecar
       itself doesn't exist yet — it's created on first save.
    3. Otherwise, raise ``StateError``. Placing the sidecar wherever the
       walk-up bottomed out would silently anchor it to the wrong root and
       break any subsequent push of files from a sibling subtree (E10 036).
    """
    start = Path(start).resolve()

    current = start
    while True:
        candidate = current / SIDECAR_DIR_NAME / SIDECAR_FILE_NAME
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent

    current = start
    while True:
        if (current / REPO_MARKER_NAME).exists():
            return current / SIDECAR_DIR_NAME / SIDECAR_FILE_NAME
        if current.parent == current:
            break
        current = current.parent

    raise StateError(
        f"No .taigun/ or .git/ found walking up from {start}. Create "
        f".taigun/ at your intended repo root before pushing "
        f"(e.g. `mkdir .taigun` next to your .git directory)."
    )


def hash_file(path: Path) -> str:
    """Content hash of the source file — the entire raw bytes.

    Format: `sha256:<64 hex>`. Prefix allows future algorithm changes.
    """
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _now_iso() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )
