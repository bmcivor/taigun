import datetime

import psycopg2.extensions
import pytest

from taigun.db.milestone import MilestoneWriter
from taigun.exceptions import (
    MilestoneConflictError,
    MilestoneMissingError,
)
from taigun.models import Milestone
from taigun.resolver import Resolver

from factories import make_project


def _push_milestone(
    conn: psycopg2.extensions.connection, **overrides
) -> int:
    """Insert a milestone via the writer and return its id."""
    today = datetime.date.today()
    defaults = {
        "project": "test-project",
        "subject": "Sprint 1",
        "estimated_start": today,
        "estimated_finish": today + datetime.timedelta(days=14),
    }
    defaults.update(overrides)
    return MilestoneWriter(conn, Resolver(conn)).write(
        Milestone(**defaults), "admin",
    )


class TestMilestoneUpdate:
    def test_updates_dates_and_closed(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: milestone inserted with a date range and closed=False.
        Expectations: update rewrites both dates and flips closed to True.
        """
        make_project(real_conn)
        milestone_id = _push_milestone(real_conn)

        new_start = datetime.date(2027, 1, 1)
        new_finish = datetime.date(2027, 1, 15)

        MilestoneWriter(real_conn, Resolver(real_conn)).update(
            Milestone(
                project="test-project",
                subject="Sprint 1",
                estimated_start=new_start,
                estimated_finish=new_finish,
                closed=True,
            ),
            milestone_id=milestone_id,
            metadata_keys={"type", "project", "estimated_start",
                           "estimated_finish", "closed"},
            acting_user="admin",
            last_pushed_at=_now_iso(),
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT estimated_start, estimated_finish, closed"
                " FROM milestones_milestone WHERE id = %s",
                (milestone_id,),
            )
            row = cur.fetchone()

        assert row == (new_start, new_finish, True)

    def test_missing_id_raises(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: project exists but no milestone with this id.
        Expectations: MilestoneMissingError raised.
        """
        make_project(real_conn)
        today = datetime.date.today()

        with pytest.raises(MilestoneMissingError, match="milestone id 999999"):
            MilestoneWriter(real_conn, Resolver(real_conn)).update(
                Milestone(
                    project="test-project",
                    subject="Sprint 1",
                    estimated_start=today,
                    estimated_finish=today,
                ),
                milestone_id=999999,
                metadata_keys={"type", "project", "estimated_start",
                               "estimated_finish"},
                acting_user="admin",
                last_pushed_at=_now_iso(),
            )

    def test_conflict_raises_when_taiga_modified_after_last_push(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: milestone inserted; last_pushed_at set to an old time.
        Expectations: MilestoneConflictError raised.
        """
        make_project(real_conn)
        milestone_id = _push_milestone(real_conn)
        today = datetime.date.today()

        with pytest.raises(MilestoneConflictError):
            MilestoneWriter(real_conn, Resolver(real_conn)).update(
                Milestone(
                    project="test-project",
                    subject="Sprint 1",
                    estimated_start=today,
                    estimated_finish=today,
                ),
                milestone_id=milestone_id,
                metadata_keys={"type", "project", "estimated_start",
                               "estimated_finish"},
                acting_user="admin",
                last_pushed_at="2020-01-01T00:00:00Z",
            )


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
