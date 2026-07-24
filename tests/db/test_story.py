import pytest

from taigun.db.epic import EpicWriter
from taigun.db.story import StoryWriter
from taigun.models import Epic, Story
from taigun.resolver import Resolver

from factories import make_milestone, make_project


class TestStoryWriter:
    def test_returns_positive_ref(self, real_conn):
        """Setup: project exists; story has only required fields.
        Expectations: writer.write returns a positive ref number.
        """
        make_project(real_conn)
        writer = StoryWriter(real_conn, Resolver(real_conn))

        ref = writer.write(Story(project="test-project", subject="Hello"), "admin")

        assert ref > 0

    def test_resolver_finds_written_story(self, real_conn):
        """Setup: project exists; story is written.
        Expectations: Resolver.resolve_story returns the story id for the new ref.
        """
        project_id = make_project(real_conn)
        writer = StoryWriter(real_conn, Resolver(real_conn))

        ref = writer.write(Story(project="test-project", subject="Hello"), "admin")

        story_id = Resolver(real_conn).resolve_story(project_id, ref)

        assert isinstance(story_id, int) and story_id > 0

    def test_ref_is_sequential_within_project(self, real_conn):
        """Setup: project exists; two stories written in succession.
        Expectations: second ref is exactly one greater than the first.
        """
        make_project(real_conn)
        writer = StoryWriter(real_conn, Resolver(real_conn))

        ref_a = writer.write(Story(project="test-project", subject="A"), "admin")
        ref_b = writer.write(Story(project="test-project", subject="B"), "admin")

        assert ref_b == ref_a + 1

    def test_with_assignee_succeeds(self, real_conn):
        """Setup: story with assignee set to the existing admin user.
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = StoryWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Story(project="test-project", subject="Hello", assignee="admin"),
            "admin",
        )

        assert ref > 0

    def test_with_milestone_succeeds(self, real_conn):
        """Setup: project + one milestone named 'Sprint 1'.
        Expectations: writer.write returns a ref without raising.
        """
        project_id = make_project(real_conn)
        make_milestone(real_conn, project_id, "Sprint 1")
        writer = StoryWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Story(project="test-project", subject="Hello", milestone="Sprint 1"),
            "admin",
        )

        assert ref > 0

    def test_with_epic_link_succeeds(self, real_conn):
        """Setup: epic written first; story with epic ref pointing at it.
        Expectations: story write returns a ref; resolver can find the story.
        """
        project_id = make_project(real_conn)
        resolver = Resolver(real_conn)
        epic_ref = EpicWriter(real_conn, resolver).write(
            Epic(project="test-project", subject="Parent epic"), "admin"
        )

        story_ref = StoryWriter(real_conn, resolver).write(
            Story(project="test-project", subject="Linked", epic=epic_ref), "admin"
        )

        assert story_ref > 0
        assert Resolver(real_conn).resolve_story(project_id, story_ref) > 0

    def test_with_custom_status(self, real_conn):
        """Setup: story with status set to a known kanban status name.
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = StoryWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Story(project="test-project", subject="Hello", status="In progress"),
            "admin",
        )

        assert ref > 0

    def test_with_custom_priority(self, real_conn):
        """Setup: story with priority set to a known kanban priority name.
        Expectations: writer.write returns a ref without raising.
        """
        make_project(real_conn)
        writer = StoryWriter(real_conn, Resolver(real_conn))

        ref = writer.write(
            Story(project="test-project", subject="Hello", priority="High"),
            "admin",
        )

        assert ref > 0

    def test_is_closed_matches_status_on_insert(self, real_conn):
        """Setup: two stories inserted — one with default status ('New',
            open) and one with 'Done' (closed).
        Expectations: userstories_userstory.is_closed mirrors the status's
            is_closed flag for each row (fix for #56).
        """
        make_project(real_conn)
        writer = StoryWriter(real_conn, Resolver(real_conn))

        open_ref = writer.write(
            Story(project="test-project", subject="open"), "admin",
        )
        closed_ref = writer.write(
            Story(project="test-project", subject="closed", status="Done"), "admin",
        )

        with real_conn.cursor() as cur:
            cur.execute(
                "SELECT ref, is_closed FROM userstories_userstory"
                " WHERE ref IN (%s, %s) ORDER BY ref",
                (open_ref, closed_ref),
            )
            rows = cur.fetchall()

        assert rows == [(open_ref, False), (closed_ref, True)]
