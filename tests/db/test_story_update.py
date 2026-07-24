import datetime

import psycopg2.extensions
import pytest

from taigun.db.story import StoryWriter
from taigun.exceptions import (
    FieldClearedError,
    TicketConflictError,
    TicketMissingError,
)
from taigun.models import Story
from taigun.resolver import Resolver

from factories import make_project


def _push_story(conn: psycopg2.extensions.connection, **overrides) -> int:
    """Insert a story via the writer and return its ref."""
    defaults = {
        "project": "test-project",
        "subject": "Original subject",
        "description": "",
    }
    defaults.update(overrides)
    return StoryWriter(conn, Resolver(conn)).write(Story(**defaults), "admin")


class TestStoryUpdate:
    def test_updates_subject_and_description(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: story inserted; then updated with new subject and description.
        Expectations: DB row reflects the new values.
        """
        project_id = make_project(real_conn)
        ref = _push_story(real_conn)

        StoryWriter(real_conn, Resolver(real_conn)).update(
            Story(
                project="test-project",
                subject="Updated subject",
                description="Body content",
            ),
            ref=ref,
            metadata_keys={"type", "project"},
            acting_user="admin",
            last_pushed_at=_now_iso(),
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT subject, description FROM userstories_userstory"
                " WHERE project_id = %s AND ref = %s",
                (project_id, ref),
            )
            row = cur.fetchone()

        assert row == ("Updated subject", "Body content")

    def test_missing_ref_raises(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: project exists but no story with this ref.
        Expectations: TicketMissingError raised.
        """
        make_project(real_conn)

        with pytest.raises(TicketMissingError, match="story #99999"):
            StoryWriter(real_conn, Resolver(real_conn)).update(
                Story(project="test-project", subject="s"),
                ref=99999,
                metadata_keys={"type", "project"},
                acting_user="admin",
                last_pushed_at=_now_iso(),
            )

    def test_conflict_raises_when_taiga_modified_after_last_push(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: story inserted, then last_pushed_at set to an old time.
        Expectations: TicketConflictError raised.
        """
        make_project(real_conn)
        ref = _push_story(real_conn)

        old = "2020-01-01T00:00:00Z"

        with pytest.raises(TicketConflictError):
            StoryWriter(real_conn, Resolver(real_conn)).update(
                Story(project="test-project", subject="s"),
                ref=ref,
                metadata_keys={"type", "project"},
                acting_user="admin",
                last_pushed_at=old,
            )

    def test_conflict_bypassed_with_ignore_conflict(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: same as above; ignore_conflict=True.
        Expectations: update succeeds, DB row updated.
        """
        make_project(real_conn)
        ref = _push_story(real_conn, subject="Original")

        StoryWriter(real_conn, Resolver(real_conn)).update(
            Story(project="test-project", subject="Overwritten"),
            ref=ref,
            metadata_keys={"type", "project"},
            acting_user="admin",
            last_pushed_at="2020-01-01T00:00:00Z",
            ignore_conflict=True,
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT subject FROM userstories_userstory WHERE ref = %s",
                (ref,),
            )
            (subject,) = cur.fetchone()

        assert subject == "Overwritten"

    def test_cleared_field_raises(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: story with assignee=admin; then updated with no assignee key
            in metadata (so field appears "omitted" — per ADR-004 that's an error).
        Expectations: FieldClearedError naming 'assignee'.
        """
        make_project(real_conn)
        ref = _push_story(real_conn, assignee="admin")

        with pytest.raises(FieldClearedError, match="assignee"):
            StoryWriter(real_conn, Resolver(real_conn)).update(
                Story(project="test-project", subject="s"),
                ref=ref,
                metadata_keys={"type", "project"},
                acting_user="admin",
                last_pushed_at=_now_iso(),
            )

    def test_explicit_null_clears_field(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: story with assignee=admin; update with assignee key in
            metadata but value is None (explicit null).
        Expectations: assigned_to_id cleared to NULL in DB.
        """
        project_id = make_project(real_conn)
        ref = _push_story(real_conn, assignee="admin")

        StoryWriter(real_conn, Resolver(real_conn)).update(
            Story(project="test-project", subject="s", assignee=None),
            ref=ref,
            metadata_keys={"type", "project", "assignee"},
            acting_user="admin",
            last_pushed_at=_now_iso(),
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT assigned_to_id FROM userstories_userstory WHERE ref = %s",
                (ref,),
            )
            (assigned_to_id,) = cur.fetchone()

        assert assigned_to_id is None

    def test_update_syncs_is_closed_when_status_changes(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: story inserted with default (open) status; updated to
            'Done' (closed).
        Expectations: userstories_userstory.is_closed flips from false to
            true — the UPDATE writes the status's is_closed flag (fix #56).
        """
        make_project(real_conn)
        ref = _push_story(real_conn)

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT is_closed FROM userstories_userstory WHERE ref = %s",
                (ref,),
            )
            assert cur.fetchone() == (False,)

        StoryWriter(real_conn, Resolver(real_conn)).update(
            Story(project="test-project", subject="s", status="Done"),
            ref=ref,
            metadata_keys={"type", "project", "status"},
            acting_user="admin",
            last_pushed_at=_now_iso(),
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT is_closed FROM userstories_userstory WHERE ref = %s",
                (ref,),
            )
            assert cur.fetchone() == (True,)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
