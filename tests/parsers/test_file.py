import pytest
from taigun.exceptions import ParseError
from taigun.parsers.file import FileParser
from taigun.models import Story, Issue, Task, Epic


FRONTMATTER_STORY = "---\ntype: story\nproject: p\n---\n\n"
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
            FRONTMATTER_STORY
            + "## Do the thing\n\n"
            "### Acceptance Criteria\n- it works\n"
        )
        result = self.parser.parse(f)

        assert isinstance(result, Story)
        assert result.subject == "Do the thing"
        assert result.description == "### Acceptance Criteria\n- it works"

    def test_missing_title_raises(self, tmp_path):
        """Setup: markdown file with no ## Title in body.
        Expectations: ParseError raised.
        """
        f = tmp_path / "ticket.md"
        f.write_text(FRONTMATTER_STORY + "### Some Section\nContent\n")
        with pytest.raises(ParseError):
            self.parser.parse(f)

    def test_priority_from_body_sets_field(self, tmp_path):
        """Setup: story file with ### Priority section in body.
        Expectations: priority field on returned model reflects body value.
        """
        f = tmp_path / "ticket.md"
        f.write_text(
            FRONTMATTER_STORY
            + "## Title\n\n"
            "### Priority\nHigh\n"
        )
        result = self.parser.parse(f)

        assert result.priority == "High"

    def test_body_priority_overrides_frontmatter(self, tmp_path):
        """Setup: story with priority in both frontmatter and ### Priority section.
        Expectations: body value wins.
        """
        f = tmp_path / "ticket.md"
        f.write_text(
            "---\ntype: story\nproject: p\npriority: Low\n---\n\n"
            "## Title\n\n"
            "### Priority\nHigh\n"
        )
        result = self.parser.parse(f)

        assert result.priority == "High"

    def test_epic_priority_section_ignored(self, tmp_path):
        """Setup: epic file with ### Priority section in body.
        Expectations: no error raised; Epic has no priority field.
        """
        f = tmp_path / "ticket.md"
        f.write_text(
            FRONTMATTER_EPIC
            + "## Epic Title\n\n"
            "### Priority\nHigh\n"
        )
        result = self.parser.parse(f)

        assert isinstance(result, Epic)
        assert not hasattr(result, "priority")

    def test_task_priority_section_ignored(self, tmp_path):
        """Setup: task file with ### Priority section in body.
        Expectations: no error raised; Task has no priority field.
        """
        f = tmp_path / "ticket.md"
        f.write_text(
            FRONTMATTER_TASK
            + "## Task Title\n\n"
            "### Priority\nHigh\n"
        )
        result = self.parser.parse(f)

        assert isinstance(result, Task)
        assert not hasattr(result, "priority")

    def test_description_excludes_priority_section(self, tmp_path):
        """Setup: story file with ### Priority and other sections.
        Expectations: description contains other sections, not Priority.
        """
        f = tmp_path / "ticket.md"
        f.write_text(
            FRONTMATTER_STORY
            + "## Title\n\n"
            "### Acceptance Criteria\n- done\n\n"
            "### Priority\nHigh\n"
        )
        result = self.parser.parse(f)

        assert result.description == "### Acceptance Criteria\n- done"
