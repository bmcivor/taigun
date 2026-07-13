import datetime

import psycopg2.extensions

from taigun.db.issue import IssueWriter
from taigun.models import Issue
from taigun.resolver import Resolver

from factories import make_project


class TestIssueUpdate:
    def test_updates_subject_and_priority(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: issue inserted with priority=Normal.
        Expectations: update to priority=High reflects in DB.
        """
        make_project(real_conn)
        ref = IssueWriter(real_conn, Resolver(real_conn)).write(
            Issue(project="test-project", subject="Broken", priority="Normal"),
            "admin",
        )

        IssueWriter(real_conn, Resolver(real_conn)).update(
            Issue(
                project="test-project",
                subject="Broken (updated)",
                priority="High",
            ),
            ref=ref,
            metadata_keys={"type", "project", "priority"},
            acting_user="admin",
            last_pushed_at=_now_iso(),
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT i.subject, p.name FROM issues_issue i"
                " JOIN projects_priority p ON i.priority_id = p.id"
                " WHERE i.ref = %s",
                (ref,),
            )
            row = cur.fetchone()

        assert row == ("Broken (updated)", "High")


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
