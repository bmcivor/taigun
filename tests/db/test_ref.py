import pytest

from taigun.db import RefAllocator
from taigun.resolver import Resolver

from factories import make_project


@pytest.mark.xfail(reason="ticket 023: references_reference INSERT missing required column(s)")
class TestRefAllocator:
    def test_returns_positive_ref(self, real_conn):
        """Setup: project exists (sequence created by ProjectCreator).
        Expectations: allocate returns a positive ref.
        """
        project_id = make_project(real_conn)
        content_type_id = Resolver(real_conn).resolve_content_type("userstories", "userstory")

        ref = RefAllocator(real_conn).allocate(project_id, 1, content_type_id)

        assert ref > 0

    def test_refs_are_sequential_for_same_project(self, real_conn):
        """Setup: same project, two allocations.
        Expectations: second ref is exactly one greater than the first.
        """
        project_id = make_project(real_conn)
        content_type_id = Resolver(real_conn).resolve_content_type("userstories", "userstory")
        allocator = RefAllocator(real_conn)

        ref_a = allocator.allocate(project_id, 1, content_type_id)
        ref_b = allocator.allocate(project_id, 2, content_type_id)

        assert ref_b == ref_a + 1


class TestRefAllocatorMissingSequence:
    def test_missing_sequence_raises_system_exit(self, real_conn):
        """Setup: project ID with no corresponding ref sequence.
        Expectations: SystemExit raised with project ID in the message.
        """
        with pytest.raises(SystemExit, match="project 99999"):
            RefAllocator(real_conn).allocate(99999, 1, 1)
