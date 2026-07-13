from pathlib import Path

import pytest

from taigun.state import (
    StateEntry,
    StateError,
    StateFile,
    hash_file,
    locate_sidecar,
)


class TestStateFileLoad:
    def test_missing_file_is_empty(self, tmp_path: Path) -> None:
        """Setup: sidecar path pointing at a non-existent file.
        Expectations: load succeeds, in-memory entries are empty.
        """
        sidecar = tmp_path / ".taigun" / "state.yaml"
        state = StateFile(sidecar)

        state.load()

        assert state.find(tmp_path / "any.md") is None

    def test_loads_valid_entries(self, tmp_path: Path) -> None:
        """Setup: sidecar with one well-formed entry.
        Expectations: find() returns it, fields intact.
        """
        sidecar = tmp_path / ".taigun" / "state.yaml"
        sidecar.parent.mkdir()
        sidecar.write_text(
            "entries:\n"
            "  - file_path: docs/foo.md\n"
            "    project: my-project\n"
            "    ref: 42\n"
            "    ticket_type: story\n"
            "    last_pushed_at: 2026-07-08T10:00:00Z\n"
            "    content_hash: sha256:abc123\n"
        )
        state = StateFile(sidecar)
        state.load()

        entry = state.find(tmp_path / "docs" / "foo.md")

        assert entry is not None
        assert entry.file_path == "docs/foo.md"
        assert entry.project == "my-project"
        assert entry.ref == 42
        assert entry.ticket_type == "story"
        assert entry.content_hash == "sha256:abc123"

    def test_malformed_yaml_raises(self, tmp_path: Path) -> None:
        """Setup: sidecar contains invalid YAML.
        Expectations: StateError raised naming YAML.
        """
        sidecar = tmp_path / ".taigun" / "state.yaml"
        sidecar.parent.mkdir()
        sidecar.write_text("entries: [ this is not valid yaml : :")
        state = StateFile(sidecar)

        with pytest.raises(StateError, match="malformed"):
            state.load()

    def test_duplicate_file_path_raises(self, tmp_path: Path) -> None:
        """Setup: sidecar has two entries with the same file_path.
        Expectations: StateError naming the duplicate path.
        """
        sidecar = tmp_path / ".taigun" / "state.yaml"
        sidecar.parent.mkdir()
        sidecar.write_text(
            "entries:\n"
            "  - file_path: docs/foo.md\n"
            "    project: p\n"
            "    ref: 1\n"
            "    ticket_type: story\n"
            "    last_pushed_at: 2026-07-08T10:00:00Z\n"
            "    content_hash: sha256:aaa\n"
            "  - file_path: docs/foo.md\n"
            "    project: p\n"
            "    ref: 2\n"
            "    ticket_type: story\n"
            "    last_pushed_at: 2026-07-08T11:00:00Z\n"
            "    content_hash: sha256:bbb\n"
        )
        state = StateFile(sidecar)

        with pytest.raises(StateError, match="Duplicate"):
            state.load()

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        """Setup: sidecar entry missing the `ref` field.
        Expectations: StateError naming the missing field.
        """
        sidecar = tmp_path / ".taigun" / "state.yaml"
        sidecar.parent.mkdir()
        sidecar.write_text(
            "entries:\n"
            "  - file_path: docs/foo.md\n"
            "    project: p\n"
            "    ticket_type: story\n"
            "    last_pushed_at: 2026-07-08T10:00:00Z\n"
            "    content_hash: sha256:aaa\n"
        )
        state = StateFile(sidecar)

        with pytest.raises(StateError, match="ref"):
            state.load()


class TestStateFileRecordAndSave:
    def test_record_then_save_persists(self, tmp_path: Path) -> None:
        """Setup: empty sidecar, record one entry, save.
        Expectations: reloading finds the same entry.
        """
        sidecar = tmp_path / ".taigun" / "state.yaml"
        state = StateFile(sidecar)
        state.load()

        source = tmp_path / "docs" / "epic.md"
        source.parent.mkdir()
        source.write_text("---\ntype: epic\nproject: p\n---\n\n## Title\n")

        state.record(
            source,
            project="my-project",
            ref=7,
            ticket_type="epic",
            content_hash="sha256:deadbeef",
        )
        state.save()

        reloaded = StateFile(sidecar)
        reloaded.load()
        entry = reloaded.find(source)

        assert entry is not None
        assert entry.ref == 7
        assert entry.project == "my-project"
        assert entry.ticket_type == "epic"
        assert entry.content_hash == "sha256:deadbeef"

    def test_record_replaces_existing(self, tmp_path: Path) -> None:
        """Setup: record twice for the same source file.
        Expectations: second record wins; only one entry persists.
        """
        sidecar = tmp_path / ".taigun" / "state.yaml"
        state = StateFile(sidecar)
        state.load()

        source = tmp_path / "docs" / "foo.md"
        source.parent.mkdir()
        source.write_text("x")

        state.record(source, "p", 1, "story", "sha256:aaa")
        state.record(source, "p", 2, "story", "sha256:bbb")
        state.save()

        reloaded = StateFile(sidecar)
        reloaded.load()
        entry = reloaded.find(source)

        assert entry is not None
        assert entry.ref == 2

    def test_record_creates_sidecar_directory(self, tmp_path: Path) -> None:
        """Setup: sidecar path with a non-existent .taigun/ parent.
        Expectations: save creates the directory.
        """
        sidecar = tmp_path / ".taigun" / "state.yaml"
        state = StateFile(sidecar)
        state.load()

        source = tmp_path / "foo.md"
        source.write_text("x")
        state.record(source, "p", 1, "story", "sha256:aaa")
        state.save()

        assert sidecar.parent.is_dir()
        assert sidecar.exists()

    def test_record_stores_path_relative_to_sidecar_dir(self, tmp_path: Path) -> None:
        """Setup: source file at tmp_path/docs/foo.md; sidecar at tmp_path/.taigun/.
        Expectations: file_path stored as `docs/foo.md`, portable across machines.
        """
        sidecar = tmp_path / ".taigun" / "state.yaml"
        source = tmp_path / "docs" / "foo.md"
        source.parent.mkdir()
        source.write_text("x")
        state = StateFile(sidecar)
        state.load()

        state.record(source, "p", 1, "story", "sha256:aaa")
        state.save()

        content = sidecar.read_text()
        assert "docs/foo.md" in content
        assert str(source) not in content  # absolute path not stored

    def test_record_source_outside_sidecar_dir_raises(self, tmp_path: Path) -> None:
        """Setup: sidecar in tmp_path/repo/, source file in tmp_path/other/.
        Expectations: StateError — source must be inside the sidecar's repo.
        """
        repo = tmp_path / "repo"
        repo.mkdir()
        other = tmp_path / "other"
        other.mkdir()
        source = other / "foo.md"
        source.write_text("x")

        sidecar = repo / ".taigun" / "state.yaml"
        state = StateFile(sidecar)
        state.load()

        with pytest.raises(StateError, match="not inside"):
            state.record(source, "p", 1, "story", "sha256:aaa")


class TestLocateSidecar:
    def test_finds_existing_sidecar_walking_up(self, tmp_path: Path) -> None:
        """Setup: sidecar at repo root, start walking from a nested directory.
        Expectations: locate_sidecar returns the actual sidecar path.
        """
        sidecar = tmp_path / ".taigun" / "state.yaml"
        sidecar.parent.mkdir()
        sidecar.write_text("entries: []\n")

        nested = tmp_path / "docs" / "epics" / "01"
        nested.mkdir(parents=True)

        found = locate_sidecar(nested)

        assert found == sidecar

    def test_no_sidecar_falls_back_to_git_repo_root(self, tmp_path: Path) -> None:
        """Setup: no `.taigun/` anywhere, but a `.git/` at ``tmp_path``.
        Expectations: locate_sidecar returns ``tmp_path/.taigun/state.yaml`` —
            the sidecar is anchored to the git root, not the starting dir.
        """
        (tmp_path / ".git").mkdir()
        nested = tmp_path / "docs" / "epics" / "01"
        nested.mkdir(parents=True)

        found = locate_sidecar(nested)

        assert found == tmp_path / ".taigun" / "state.yaml"

    def test_no_sidecar_and_no_git_raises(self, tmp_path: Path) -> None:
        """Setup: no `.taigun/` and no `.git/` anywhere on the walk-up.
        Expectations: locate_sidecar raises StateError instead of returning a
            silently-wrong default (E10 036).
        """
        with pytest.raises(StateError, match="No .taigun/ or .git/ found"):
            locate_sidecar(tmp_path)

    def test_existing_sidecar_wins_over_git_root(self, tmp_path: Path) -> None:
        """Setup: `.git/` at ``tmp_path`` AND a `.taigun/state.yaml` in a
            nested dir below.
        Expectations: locate_sidecar returns the nested sidecar (already
            established location wins over the git-root default).
        """
        (tmp_path / ".git").mkdir()
        nested = tmp_path / "docs" / "epics"
        (nested / ".taigun").mkdir(parents=True)
        (nested / ".taigun" / "state.yaml").write_text("entries: []\n")

        found = locate_sidecar(nested / "01")

        assert found == nested / ".taigun" / "state.yaml"


class TestHashFile:
    def test_hash_is_deterministic(self, tmp_path: Path) -> None:
        """Setup: two files with identical content.
        Expectations: same hash.
        """
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_bytes(b"hello world")
        b.write_bytes(b"hello world")

        assert hash_file(a) == hash_file(b)

    def test_hash_changes_with_content(self, tmp_path: Path) -> None:
        """Setup: two files with different content.
        Expectations: different hashes.
        """
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_bytes(b"one")
        b.write_bytes(b"two")

        assert hash_file(a) != hash_file(b)

    def test_hash_format(self, tmp_path: Path) -> None:
        """Setup: any file.
        Expectations: hash starts with 'sha256:' and is 64 hex chars after that.
        """
        f = tmp_path / "f.md"
        f.write_bytes(b"x")

        h = hash_file(f)

        assert h.startswith("sha256:")
        assert len(h) == len("sha256:") + 64
