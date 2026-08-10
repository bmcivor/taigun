import datetime
from pathlib import Path

import pytest

from taigun.exceptions import ParseError
from taigun.models import Issue, Milestone, Story
from taigun.parsers.file import FileParser

FRONTMATTER_STORY = "---\ntype: story\nproject: p\n---\n\n"
FRONTMATTER_ISSUE = "---\ntype: issue\nproject: p\n---\n\n"
FRONTMATTER_EPIC = "---\ntype: epic\nproject: p\n---\n\n"
FRONTMATTER_TASK = "---\ntype: task\nproject: p\n---\n\n"


class TestFileParser:
    def setup_method(self):
        self.parser = FileParser()

    def test_returns_populated_story(self, tmp_path):
        """Setup: markdown file with story frontmatter and body.
        Expectations: returns Story with subject and description set.
        """
        f = tmp_path / "ticket.md"
        f.write_text(
            FRONTMATTER_STORY + "## Do the thing\n\n"
            "### Acceptance Criteria\n\n- it works\n"
        )
        result = self.parser.parse(f)

        assert isinstance(result, Story)
        assert result.subject == "Do the thing"
        assert result.description == "### Acceptance Criteria\n\n- it works"

    def test_missing_title_raises(self, tmp_path):
        """Setup: markdown file with no ## Title in body.
        Expectations: ParseError raised.
        """
        f = tmp_path / "ticket.md"
        f.write_text(FRONTMATTER_STORY + "### Some Section\nContent\n")
        with pytest.raises(ParseError):
            self.parser.parse(f)

    def test_issue_body_priority_sets_field(self, tmp_path):
        """Setup: issue file with ### Priority section in body.
        Expectations: priority field on returned Issue reflects body value.
        """
        f = tmp_path / "ticket.md"
        f.write_text(FRONTMATTER_ISSUE + "## Title\n\n### Priority\nHigh\n")
        result = self.parser.parse(f)

        assert isinstance(result, Issue)
        assert result.priority == "High"

    def test_issue_body_priority_overrides_frontmatter(self, tmp_path):
        """Setup: issue with priority in both frontmatter and ### Priority section.
        Expectations: body value wins.
        """
        f = tmp_path / "ticket.md"
        f.write_text(
            "---\ntype: issue\nproject: p\npriority: Low\n---\n\n"
            "## Title\n\n"
            "### Priority\nHigh\n"
        )
        result = self.parser.parse(f)

        assert result.priority == "High"

    def test_story_body_priority_raises(self, tmp_path):
        """Setup: story file with ### Priority section in body.
        Expectations: ParseError raised — priority is only valid on issues.
        """
        f = tmp_path / "ticket.md"
        f.write_text(FRONTMATTER_STORY + "## Title\n\n### Priority\nHigh\n")
        with pytest.raises(ParseError, match="story"):
            self.parser.parse(f)

    def test_story_frontmatter_priority_raises(self, tmp_path):
        """Setup: story file with priority in frontmatter.
        Expectations: ParseError raised — priority is only valid on issues.
        """
        f = tmp_path / "ticket.md"
        f.write_text("---\ntype: story\nproject: p\npriority: High\n---\n\n## Title\n")
        with pytest.raises(ParseError, match="story"):
            self.parser.parse(f)

    def test_task_body_priority_raises(self, tmp_path):
        """Setup: task file with ### Priority section in body.
        Expectations: ParseError raised — priority is only valid on issues.
        """
        f = tmp_path / "ticket.md"
        f.write_text(FRONTMATTER_TASK + "## Task Title\n\n### Priority\nHigh\n")
        with pytest.raises(ParseError, match="task"):
            self.parser.parse(f)

    def test_epic_body_priority_raises(self, tmp_path):
        """Setup: epic file with ### Priority section in body.
        Expectations: ParseError raised — priority is only valid on issues.
        """
        f = tmp_path / "ticket.md"
        f.write_text(FRONTMATTER_EPIC + "## Epic Title\n\n### Priority\nHigh\n")
        with pytest.raises(ParseError, match="epic"):
            self.parser.parse(f)

    def test_issue_description_excludes_priority_section(self, tmp_path):
        """Setup: issue file with ### Priority and other sections.
        Expectations: description contains other sections, not Priority.
        """
        f = tmp_path / "ticket.md"
        f.write_text(
            FRONTMATTER_ISSUE + "## Title\n\n"
            "### Acceptance Criteria\n\n- done\n\n"
            "### Priority\nHigh\n"
        )
        result = self.parser.parse(f)

        assert result.description == "### Acceptance Criteria\n\n- done"

    def test_story_user_story_preamble_in_description(self, tmp_path):
        """Setup: story file with As a / I want / So that block above first ### heading.
        Expectations: description preserves the preamble verbatim at the start.
        """
        f = tmp_path / "ticket.md"
        f.write_text(
            FRONTMATTER_STORY + "## Title\n\n"
            "**As a** dev\n"
            "**I want** something\n"
            "**So that** reason\n\n"
            "### Acceptance Criteria\n\n- done\n"
        )
        result = self.parser.parse(f)

        assert result.description == (
            "**As a** dev\n"
            "**I want** something\n"
            "**So that** reason\n\n"
            "### Acceptance Criteria\n\n- done"
        )

    def test_milestone_basic(self, tmp_path: Path) -> None:
        """Setup: milestone file with only required fields.
        Expectations: returns Milestone with subject, dates, and closed=False.
        """
        f = tmp_path / "sprint.md"
        f.write_text(
            "---\ntype: milestone\nproject: p\n"
            "estimated_start: 2026-08-01\n"
            "estimated_finish: 2026-08-14\n---\n\n"
            "## Sprint 3\n"
        )
        result = self.parser.parse(f)

        assert isinstance(result, Milestone)
        assert result.subject == "Sprint 3"
        assert result.estimated_start == datetime.date(2026, 8, 1)
        assert result.estimated_finish == datetime.date(2026, 8, 14)
        assert result.closed is False
        assert result.assignee is None

    def test_milestone_with_optional_fields(self, tmp_path: Path) -> None:
        """Setup: milestone file with closed and assignee set.
        Expectations: those fields populated on the returned Milestone.
        """
        f = tmp_path / "sprint.md"
        f.write_text(
            "---\ntype: milestone\nproject: p\n"
            "estimated_start: 2026-08-01\n"
            "estimated_finish: 2026-08-14\n"
            "closed: true\n"
            "assignee: bmcivor\n---\n\n"
            "## Sprint 1\n"
        )
        result = self.parser.parse(f)

        assert result.closed is True
        assert result.assignee == "bmcivor"

    def test_milestone_missing_dates_raises(self, tmp_path: Path) -> None:
        """Setup: milestone file missing estimated_finish.
        Expectations: ParseError naming the missing field.
        """
        f = tmp_path / "sprint.md"
        f.write_text(
            "---\ntype: milestone\nproject: p\n"
            "estimated_start: 2026-08-01\n---\n\n"
            "## Sprint 3\n"
        )
        with pytest.raises(ParseError, match="estimated_finish"):
            self.parser.parse(f)

    def test_milestone_body_beyond_title_raises(self, tmp_path: Path) -> None:
        """Setup: milestone file with content after the ## Title.
        Expectations: ParseError — schema has no description for milestones.
        """
        f = tmp_path / "sprint.md"
        f.write_text(
            "---\ntype: milestone\nproject: p\n"
            "estimated_start: 2026-08-01\n"
            "estimated_finish: 2026-08-14\n---\n\n"
            "## Sprint 3\n\n"
            "### Notes\n\nsome extra text\n"
        )
        with pytest.raises(ParseError, match="only the `## Title`"):
            self.parser.parse(f)
