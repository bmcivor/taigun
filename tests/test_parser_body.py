import pytest
from taigun.exceptions import ParseError
from taigun.parsers.body import BodyParser
from taigun.parsers.file import FileParser
from taigun.models import Story, Issue, Task, Epic


FRONTMATTER_STORY = "---\ntype: story\nproject: p\n---\n\n"
FRONTMATTER_EPIC = "---\ntype: epic\nproject: p\n---\n\n"
FRONTMATTER_TASK = "---\ntype: task\nproject: p\n---\n\n"


class TestBodyParserParse:
    def setup_method(self):
        self.parser = BodyParser()

    def test_extracts_subject(self):
        """Setup: body with a ## Title heading.
        Expectations: subject is the heading text without the ## prefix.
        """
        subject, _, _ = self.parser.parse("## My Ticket Title\n")
        assert subject == "My Ticket Title"

    def test_missing_title_raises(self):
        """Setup: body with no ## heading.
        Expectations: ParseError raised.
        """
        with pytest.raises(ParseError):
            self.parser.parse("### Some Section\nContent\n")

    def test_priority_extracted(self):
        """Setup: body with a ### Priority section.
        Expectations: priority value returned, section absent from description.
        """
        body = "## Title\n\n### Priority\nHigh\n"
        _, description, priority = self.parser.parse(body)
        assert priority == "High"
        assert "Priority" not in description

    def test_no_priority_section(self):
        """Setup: body with no ### Priority section.
        Expectations: priority is None.
        """
        body = "## Title\n\n### Acceptance Criteria\n- foo\n"
        _, _, priority = self.parser.parse(body)
        assert priority is None

    def test_other_sections_in_description(self):
        """Setup: body with a non-priority ### section.
        Expectations: section heading and content present in description.
        """
        body = "## Title\n\n### Acceptance Criteria\n- foo\n- bar\n"
        _, description, _ = self.parser.parse(body)
        assert "### Acceptance Criteria" in description
        assert "- foo" in description
        assert "- bar" in description

    def test_multiple_sections_assembled_in_order(self):
        """Setup: body with multiple ### sections.
        Expectations: all sections in description in original order.
        """
        body = (
            "## Title\n\n"
            "### User Story\nAs a dev\n\n"
            "### Acceptance Criteria\n- done\n"
        )
        _, description, _ = self.parser.parse(body)
        assert description.index("### User Story") < description.index("### Acceptance Criteria")

    def test_priority_not_in_description(self):
        """Setup: body with ### Priority among other sections.
        Expectations: description contains other sections but not Priority.
        """
        body = (
            "## Title\n\n"
            "### User Story\nAs a dev\n\n"
            "### Priority\nHigh\n\n"
            "### Acceptance Criteria\n- done\n"
        )
        _, description, priority = self.parser.parse(body)
        assert priority == "High"
        assert "### Priority" not in description
        assert "### User Story" in description
        assert "### Acceptance Criteria" in description

    def test_empty_priority_section_returns_none(self):
        """Setup: ### Priority section with no content.
        Expectations: priority is None.
        """
        body = "## Title\n\n### Priority\n\n"
        _, _, priority = self.parser.parse(body)
        assert priority is None


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
        assert "### Acceptance Criteria" in result.description
        assert "it works" in result.description

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
        assert "### Acceptance Criteria" in result.description
        assert "### Priority" not in result.description
