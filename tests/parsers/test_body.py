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

    def test_no_priority_section(self):
        """Setup: body with no ### Priority section.
        Expectations: priority is None.
        """
        body = "## Title\n\n### Acceptance Criteria\n- foo\n"
        _, _, priority = self.parser.parse(body)

        assert priority is None

    def test_other_sections_in_description(self):
        """Setup: body with a non-priority ### section.
        Expectations: description is the section heading and content verbatim.
        """
        body = "## Title\n\n### Acceptance Criteria\n- foo\n- bar\n"
        _, description, _ = self.parser.parse(body)

        assert description == "### Acceptance Criteria\n- foo\n- bar"

    def test_multiple_sections_assembled_in_order(self):
        """Setup: body with multiple ### sections.
        Expectations: description is both sections joined by a blank line in original order.
        """
        body = (
            "## Title\n\n"
            "### User Story\nAs a dev\n\n"
            "### Acceptance Criteria\n- done\n"
        )
        _, description, _ = self.parser.parse(body)

        assert description == "### User Story\nAs a dev\n\n### Acceptance Criteria\n- done"

    def test_priority_not_in_description(self):
        """Setup: body with ### Priority among other sections.
        Expectations: priority extracted, description is the remaining sections joined by a blank line.
        """
        body = (
            "## Title\n\n"
            "### User Story\nAs a dev\n\n"
            "### Priority\nHigh\n\n"
            "### Acceptance Criteria\n- done\n"
        )
        _, description, priority = self.parser.parse(body)

        assert priority == "High"
        assert description == "### User Story\nAs a dev\n\n### Acceptance Criteria\n- done"

    def test_empty_priority_section_returns_none(self):
        """Setup: ### Priority section with no content.
        Expectations: priority is None.
        """
        body = "## Title\n\n### Priority\n\n"
        _, _, priority = self.parser.parse(body)

        assert priority is None
