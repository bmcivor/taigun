import datetime

import psycopg2.extensions

from taigun.db.milestone import MilestoneWriter
from taigun.models import Milestone
from taigun.resolver import Resolver

from factories import make_project


class TestMilestoneWriter:
    def test_returns_positive_id(self, real_conn: psycopg2.extensions.connection) -> None:
        """Setup: project exists; milestone with only required fields.
        Expectations: writer.write returns a positive milestone id.
        """
        project_id = make_project(real_conn)
        writer = MilestoneWriter(real_conn, Resolver(real_conn))
        today = datetime.date.today()

        milestone_id = writer.write(
            Milestone(
                project="test-project",
                subject="Sprint 1",
                estimated_start=today,
                estimated_finish=today + datetime.timedelta(days=14),
            ),
            "admin",
        )

        assert milestone_id > 0

    def test_writes_expected_columns(self, real_conn: psycopg2.extensions.connection) -> None:
        """Setup: milestone written with all fields set.
        Expectations: DB row matches the model values, slug derived from name.
        """
        project_id = make_project(real_conn)
        writer = MilestoneWriter(real_conn, Resolver(real_conn))
        start = datetime.date(2026, 8, 1)
        finish = datetime.date(2026, 8, 14)

        milestone_id = writer.write(
            Milestone(
                project="test-project",
                subject="Sprint 3",
                estimated_start=start,
                estimated_finish=finish,
                closed=False,
            ),
            "admin",
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT name, slug, estimated_start, estimated_finish, closed, project_id"
                " FROM milestones_milestone WHERE id = %s",
                (milestone_id,),
            )
            row = cur.fetchone()

        assert row == ("Sprint 3", "sprint-3", start, finish, False, project_id)

    def test_order_is_sequential(self, real_conn: psycopg2.extensions.connection) -> None:
        """Setup: two milestones written back to back on the same project.
        Expectations: second gets order = first + 1.
        """
        project_id = make_project(real_conn)
        writer = MilestoneWriter(real_conn, Resolver(real_conn))
        today = datetime.date.today()

        writer.write(
            Milestone(project="test-project", subject="Sprint 1",
                      estimated_start=today, estimated_finish=today),
            "admin",
        )
        writer.write(
            Milestone(project="test-project", subject="Sprint 2",
                      estimated_start=today, estimated_finish=today),
            "admin",
        )

        with real_conn.cursor() as cur:
            cur.execute(
                'SELECT name, "order" FROM milestones_milestone'
                " WHERE project_id = %s ORDER BY \"order\"",
                (project_id,),
            )
            rows = cur.fetchall()

        assert [n for n, _ in rows] == ["Sprint 1", "Sprint 2"]
        assert rows[1][1] == rows[0][1] + 1

    def test_owner_defaults_to_acting_user(self, real_conn: psycopg2.extensions.connection) -> None:
        """Setup: milestone written with no assignee.
        Expectations: owner_id resolves to the acting user.
        """
        project_id = make_project(real_conn)
        writer = MilestoneWriter(real_conn, Resolver(real_conn))
        today = datetime.date.today()

        milestone_id = writer.write(
            Milestone(project="test-project", subject="Sprint 1",
                      estimated_start=today, estimated_finish=today),
            "admin",
        )

        admin_id = Resolver(real_conn).resolve_user("admin")
        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT owner_id FROM milestones_milestone WHERE id = %s",
                (milestone_id,),
            )
            (owner_id,) = cur.fetchone()

        assert owner_id == admin_id
