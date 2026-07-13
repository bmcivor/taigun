import datetime
import re
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from taigun.cli import app
from taigun.config import ConfigManager, Profile
from taigun.db.project import ProjectCreator
from taigun.resolver import Resolver

runner = CliRunner()


def unique_slug() -> str:
    return f"test-{uuid.uuid4().hex[:8]}"


def write_ticket(tmp_path: Path, name: str, ticket_type: str, project_slug: str, subject: str = "The subject") -> Path:
    """Write a minimal valid markdown ticket file and return its path."""
    content = f"---\ntype: {ticket_type}\nproject: {project_slug}\n---\n\n## {subject}\n"
    path = tmp_path / name
    path.write_text(content)
    return path


def make_config(tmp_path: Path, profile) -> ConfigManager:
    """Save ``profile`` under ``tmp_path/config.toml`` and mark ``tmp_path``
    as a repo root so ``locate_sidecar`` anchors the sidecar under it
    instead of walking up out of the temp tree.
    """
    (tmp_path / ".git").mkdir(exist_ok=True)
    config = ConfigManager(path=tmp_path / "config.toml")
    config.save(profile, name=None)
    return config


@contextmanager
def patch_config(config: ConfigManager):
    with patch("taigun.cli.ConfigManager", return_value=config):
        yield config


def _ref_from_insert_output(output: str) -> int:
    """Extract the numeric ref from a push insert line (``✓ #<ref> ...``)."""
    match = re.search(r"#(\d+)", output)
    assert match is not None, f"expected ref in output: {output!r}"
    return int(match.group(1))


class TestPushParseErrors:
    """Parse errors fail before any writer/connection logic, so they don't need
    project setup and don't xfail."""

    def test_exit_one_on_parse_error(self, tmp_path, test_db_profile):
        """Setup: ticket file with malformed frontmatter (missing project).
        Expectations: exit code 1.
        """
        config = make_config(tmp_path, test_db_profile)
        bad = tmp_path / "bad.md"
        bad.write_text("---\ntype: story\n---\n\n## Title\n")

        with patch_config(config):
            result = runner.invoke(app, ["push", str(bad)])

        assert result.exit_code == 1

    def test_parse_error_output_format(self, tmp_path, test_db_profile):
        """Setup: malformed ticket file named 'broken.md'.
        Expectations: error line starts with '✗ broken.md:' (filename precisely).
        """
        config = make_config(tmp_path, test_db_profile)
        bad = tmp_path / "broken.md"
        bad.write_text("---\ntype: story\n---\n\n## Title\n")

        with patch_config(config):
            result = runner.invoke(app, ["push", str(bad)])

        lines = result.output.splitlines()
        assert any(line.startswith("✗ broken.md:") for line in lines)


class TestPushSuccess:
    def test_pushes_single_story(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project exists; valid story ticket file.
        Expectations: output is exactly one success line matching the format
            `✓ #<ref> story: "Hello"` (ref is dynamic so use endswith).
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Test Project", slug, "admin")
        config = make_config(tmp_path, test_db_profile)
        ticket = write_ticket(tmp_path, "ticket.md", "story", slug, subject="Hello")

        with patch_config(config):
            result = runner.invoke(app, ["push", str(ticket)])

        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert len(lines) == 1
        assert lines[0].startswith("✓ #") and lines[0].endswith(' story: "Hello"')

    def test_pushes_multiple_files(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project exists; two valid ticket files.
        Expectations: two success lines; exit 0.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Test Project", slug, "admin")
        config = make_config(tmp_path, test_db_profile)
        a = write_ticket(tmp_path, "a.md", "story", slug, subject="A")
        b = write_ticket(tmp_path, "b.md", "story", slug, subject="B")

        with patch_config(config):
            result = runner.invoke(app, ["push", str(a), str(b)])

        assert result.exit_code == 0
        assert result.output.count("✓") == 2

    def test_dry_run_outputs_tilde_marker(self, tmp_path, test_db_profile, cli_conn):
        """Setup: --dry-run; project exists; valid ticket file.
        Expectations: output is exactly `~ story: "Dry"` (no ref, no ✓).
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Test Project", slug, "admin")
        config = make_config(tmp_path, test_db_profile)
        ticket = write_ticket(tmp_path, "ticket.md", "story", slug, subject="Dry")

        with patch_config(config):
            result = runner.invoke(app, ["push", "--dry-run", str(ticket)])

        assert result.exit_code == 0
        assert result.output == '~ story: "Dry"\n'

    def test_partial_failure_exits_one(self, tmp_path, test_db_profile, cli_conn):
        """Setup: project committed; one valid ticket and one malformed file.
        Expectations: exit 1; output contains both a success line and an
            error line for the bad file.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Test Project", slug, "admin")
        config = make_config(tmp_path, test_db_profile)
        good = write_ticket(tmp_path, "good.md", "story", slug, subject="Good")
        bad = tmp_path / "bad.md"
        bad.write_text("---\ntype: story\n---\n\n## Title\n")

        with patch_config(config):
            result = runner.invoke(app, ["push", str(good), str(bad)])

        assert result.exit_code == 1
        assert result.output.count("✓") == 1
        assert result.output.count("✗") == 1

    def test_profile_flag_uses_named_profile(self, tmp_path, test_db_profile, cli_conn):
        """Setup: 'work' profile saved with test-db credentials; default profile
            saved with deliberately wrong credentials. Push with --profile work.
        Expectations: exit 0 (the work profile's credentials are used).
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Test Project", slug, "admin")
        (tmp_path / ".git").mkdir()
        config = ConfigManager(path=tmp_path / "config.toml")
        bad_default = Profile(
            host="nonexistent-host",
            port=5432,
            database="taiga",
            username="taiga",
            password="taiga",
            acting_user="admin",
        )
        config.save(bad_default, name=None)
        config.save(test_db_profile, name="work")
        ticket = write_ticket(tmp_path, "ticket.md", "story", slug, subject="Hello")

        with patch_config(config):
            result = runner.invoke(app, ["push", "--profile", "work", str(ticket)])

        assert result.exit_code == 0


class TestPushUpsert:
    def test_re_push_edited_file_updates_instead_of_inserting(
        self, tmp_path, test_db_profile, cli_conn
    ):
        """Setup: push a story; edit the same file to change subject; re-push.
        Expectations: second push emits the "↺ #<ref> ... (updated)" line, no
            duplicate ticket exists in the DB.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Test Project", slug, "admin")
        config = make_config(tmp_path, test_db_profile)
        ticket = write_ticket(tmp_path, "ticket.md", "story", slug, subject="First")

        with patch_config(config):
            first = runner.invoke(app, ["push", str(ticket)])
        assert first.exit_code == 0
        ref = _ref_from_insert_output(first.output)

        ticket.write_text(
            f"---\ntype: story\nproject: {slug}\n---\n\n## Second\n"
        )

        with patch_config(config):
            second = runner.invoke(app, ["push", str(ticket)])

        assert second.exit_code == 0
        assert second.output == f'↺ #{ref} story: "Second" (updated)\n'

        with cli_conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM userstories_userstory"
                " WHERE project_id = (SELECT id FROM projects_project WHERE slug = %s)",
                (slug,),
            )
            (count,) = cur.fetchone()
        assert count == 1

    def test_re_push_unchanged_file_is_noop(
        self, tmp_path, test_db_profile, cli_conn
    ):
        """Setup: push a story; re-push the same file with no edits.
        Expectations: second push prints "(unchanged) #<ref>"; DB row's
            modified_date does not advance.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Test Project", slug, "admin")
        config = make_config(tmp_path, test_db_profile)
        ticket = write_ticket(tmp_path, "ticket.md", "story", slug, subject="Same")

        with patch_config(config):
            first = runner.invoke(app, ["push", str(ticket)])
        ref = _ref_from_insert_output(first.output)

        with cli_conn.cursor() as cur:
            cur.execute(
                "SELECT modified_date FROM userstories_userstory"
                " WHERE project_id = (SELECT id FROM projects_project WHERE slug = %s)",
                (slug,),
            )
            (before,) = cur.fetchone()

        with patch_config(config):
            second = runner.invoke(app, ["push", str(ticket)])

        assert second.exit_code == 0
        assert second.output == f'(unchanged) #{ref} story: "Same"\n'

        with cli_conn.cursor() as cur:
            cur.execute(
                "SELECT modified_date FROM userstories_userstory"
                " WHERE project_id = (SELECT id FROM projects_project WHERE slug = %s)",
                (slug,),
            )
            (after,) = cur.fetchone()
        assert before == after

    def test_re_push_with_changed_type_errors(
        self, tmp_path, test_db_profile, cli_conn
    ):
        """Setup: push a story; rewrite the file with type: epic; re-push.
        Expectations: exit 1; error message about identity change.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Test Project", slug, "admin")
        config = make_config(tmp_path, test_db_profile)
        ticket = write_ticket(tmp_path, "ticket.md", "story", slug, subject="X")

        with patch_config(config):
            runner.invoke(app, ["push", str(ticket)])

        ticket.write_text(
            f"---\ntype: epic\nproject: {slug}\n---\n\n## X\n"
        )

        with patch_config(config):
            result = runner.invoke(app, ["push", str(ticket)])

        assert result.exit_code == 1
        assert result.output == (
            "✗ ticket.md: type changed from 'story' to 'epic' — "
            "remove the sidecar entry to push as a new ticket\n"
        )

    def test_milestone_re_push_unchanged_is_noop(
        self, tmp_path, test_db_profile, cli_conn
    ):
        """Setup: push a milestone; re-push the same file with no edits.
        Expectations: second push prints '(unchanged) milestone: "Sprint 1"';
            DB row unchanged.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Test Project", slug, "admin")
        config = make_config(tmp_path, test_db_profile)
        ticket = tmp_path / "sprint.md"
        ticket.write_text(
            f"---\ntype: milestone\nproject: {slug}\n"
            f"estimated_start: 2026-08-01\nestimated_finish: 2026-08-14\n"
            f"---\n\n## Sprint 1\n"
        )

        with patch_config(config):
            first = runner.invoke(app, ["push", str(ticket)])
        assert first.exit_code == 0

        with patch_config(config):
            second = runner.invoke(app, ["push", str(ticket)])

        assert second.exit_code == 0
        assert second.output == '(unchanged) milestone: "Sprint 1"\n'

    def test_milestone_re_push_edited_file_updates(
        self, tmp_path, test_db_profile, cli_conn
    ):
        """Setup: push a milestone; edit its dates and closed flag; re-push.
        Expectations: '↺ milestone: "Sprint 1" (updated)'; DB reflects the
            new dates and closed flag.
        """
        slug = unique_slug()
        ProjectCreator(cli_conn, Resolver(cli_conn)).create("Test Project", slug, "admin")
        config = make_config(tmp_path, test_db_profile)
        ticket = tmp_path / "sprint.md"
        ticket.write_text(
            f"---\ntype: milestone\nproject: {slug}\n"
            f"estimated_start: 2026-08-01\nestimated_finish: 2026-08-14\n"
            f"---\n\n## Sprint 1\n"
        )

        with patch_config(config):
            runner.invoke(app, ["push", str(ticket)])

        ticket.write_text(
            f"---\ntype: milestone\nproject: {slug}\n"
            f"estimated_start: 2026-08-02\nestimated_finish: 2026-08-15\n"
            f"closed: true\n"
            f"---\n\n## Sprint 1\n"
        )

        with patch_config(config):
            second = runner.invoke(app, ["push", str(ticket)])

        assert second.exit_code == 0
        assert second.output == '↺ milestone: "Sprint 1" (updated)\n'

        with cli_conn.cursor() as cur:
            cur.execute(
                "SELECT estimated_start, estimated_finish, closed"
                " FROM milestones_milestone"
                " WHERE project_id = (SELECT id FROM projects_project WHERE slug = %s)",
                (slug,),
            )
            row = cur.fetchone()

        assert row == (
            datetime.date(2026, 8, 2),
            datetime.date(2026, 8, 15),
            True,
        )
