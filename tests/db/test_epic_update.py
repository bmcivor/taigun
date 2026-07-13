import datetime

import psycopg2.extensions

from taigun.db.epic import EpicWriter
from taigun.models import Epic
from taigun.resolver import Resolver

from factories import make_project


class TestEpicUpdate:
    def test_updates_subject_and_description(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: epic inserted with original values.
        Expectations: update rewrites subject/description.
        """
        make_project(real_conn)
        ref = EpicWriter(real_conn, Resolver(real_conn)).write(
            Epic(project="test-project", subject="Original"),
            "admin",
        )

        EpicWriter(real_conn, Resolver(real_conn)).update(
            Epic(project="test-project", subject="Updated", description="Body"),
            ref=ref,
            metadata_keys={"type", "project"},
            acting_user="admin",
            last_pushed_at=_now_iso(),
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT subject, description FROM epics_epic WHERE ref = %s",
                (ref,),
            )
            row = cur.fetchone()

        assert row == ("Updated", "Body")

    def test_color_preserved_when_source_omits_it(
        self, real_conn: psycopg2.extensions.connection
    ) -> None:
        """Setup: epic inserted with an explicit color; update with no color.
        Expectations: DB row retains the original color.
        """
        make_project(real_conn)
        ref = EpicWriter(real_conn, Resolver(real_conn)).write(
            Epic(project="test-project", subject="s", color="#abcdef"),
            "admin",
        )

        EpicWriter(real_conn, Resolver(real_conn)).update(
            Epic(project="test-project", subject="s"),
            ref=ref,
            metadata_keys={"type", "project"},
            acting_user="admin",
            last_pushed_at=_now_iso(),
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT color FROM epics_epic WHERE ref = %s",
                (ref,),
            )
            (color,) = cur.fetchone()

        assert color == "#abcdef"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
