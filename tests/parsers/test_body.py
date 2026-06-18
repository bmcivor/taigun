import pytest
from taigun.exceptions import ParseError
from taigun.parsers.body import BodyParser


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
        Expectations: priority value returned, description is empty.
        """
        body = "## Title\n\n### Priority\nHigh\n"
        _, description, priority = self.parser.parse(body)

        assert priority == "High"
        assert description == ""

    def test_priority_strips_list_prefix(self):
        """Setup: body with ### Priority value as a markdown list item.
        Expectations: leading '- ' stripped from the priority value.
        """
        body = "## Title\n\n### Priority\n\n- High\n"
        _, _, priority = self.parser.parse(body)

        assert priority == "High"

    def test_no_priority_section(self):
        """Setup: body with no ### Priority section.
        Expectations: priority is None.
        """
        body = "## Title\n\n### Acceptance Criteria\n- foo\n"
        _, _, priority = self.parser.parse(body)

        assert priority is None

    def test_other_sections_in_description(self):
        """Setup: body with a non-priority ### section.
        Expectations: description includes the section heading and content with blank line preserved.
        """
        body = "## Title\n\n### Acceptance Criteria\n\n- foo\n- bar\n"
        _, description, _ = self.parser.parse(body)

        assert description == "### Acceptance Criteria\n\n- foo\n- bar"

    def test_multiple_sections_assembled_in_order(self):
        """Setup: body with multiple ### sections.
        Expectations: description preserves all sections and their internal whitespace verbatim.
        """
        body = (
            "## Title\n\n"
            "### User Story\n\nAs a dev\n\n"
            "### Acceptance Criteria\n\n- done\n"
        )
        _, description, _ = self.parser.parse(body)

        assert description == "### User Story\n\nAs a dev\n\n### Acceptance Criteria\n\n- done"

    def test_priority_not_in_description(self):
        """Setup: body with ### Priority among other sections.
        Expectations: priority extracted, description preserves the remaining sections verbatim.
        """
        body = (
            "## Title\n\n"
            "### User Story\n\nAs a dev\n\n"
            "### Priority\n\nHigh\n\n"
            "### Acceptance Criteria\n\n- done\n"
        )
        _, description, priority = self.parser.parse(body)

        assert priority == "High"
        assert description == "### User Story\n\nAs a dev\n\n### Acceptance Criteria\n\n- done"

    def test_empty_priority_section_returns_none(self):
        """Setup: ### Priority section with no content.
        Expectations: priority is None.
        """
        body = "## Title\n\n### Priority\n\n"
        _, _, priority = self.parser.parse(body)

        assert priority is None

    def test_user_story_preamble_preserved(self):
        """Setup: body with As a / I want / So that block between title and first ### heading.
        Expectations: description includes the preamble verbatim at the start.
        """
        body = (
            "## Title\n\n"
            "**As a** dev\n"
            "**I want** something\n"
            "**So that** reason\n\n"
            "### Acceptance Criteria\n\n- done\n"
        )
        _, description, _ = self.parser.parse(body)

        assert description == (
            "**As a** dev\n"
            "**I want** something\n"
            "**So that** reason\n\n"
            "### Acceptance Criteria\n\n- done"
        )

    def test_blank_line_between_heading_and_content_preserved(self):
        """Setup: body with blank lines between ### heading and content.
        Expectations: blank lines preserved in description.
        """
        body = (
            "## Title\n\n"
            "### Context\n\n"
            "Background paragraph.\n\n"
            "### Acceptance Criteria\n\n"
            "- done\n"
        )
        _, description, _ = self.parser.parse(body)

        assert description == (
            "### Context\n\n"
            "Background paragraph.\n\n"
            "### Acceptance Criteria\n\n"
            "- done"
        )
