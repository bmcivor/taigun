import pytest

from taigun.db.story import StoryWriter
from taigun.models import Story
from taigun.resolver import Resolver

from factories import make_project


@pytest.mark.xfail(reason="ticket 023: writer SQL bugs not yet fixed")
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
