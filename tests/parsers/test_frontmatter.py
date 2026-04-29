import pytest
from taigun.exceptions import ParseError
from taigun.parsers.frontmatter import FrontmatterParser
from taigun.models import Story, Issue, Task, Epic


def make_doc(frontmatter: str, body: str = "## Title\n") -> str:
    return f"---\n{frontmatter}---\n\n{body}"


class TestFrontmatterParserParse:
    def setup_method(self):
        self.parser = FrontmatterParser()

    def test_missing_type_raises(self):
        """Setup: frontmatter with no type field.
        Expectations: ParseError naming 'type'.
        """
        doc = make_doc("project: my-project\n")
        with pytest.raises(ParseError, match="type"):
            self.parser.parse(doc)

    def test_missing_project_raises(self):
        """Setup: frontmatter with no project field.
        Expectations: ParseError naming 'project'.
        """
        doc = make_doc("type: story\n")
        with pytest.raises(ParseError, match="project"):
            self.parser.parse(doc)

    def test_unknown_key_raises(self):
        """Setup: frontmatter with an unrecognised key.
        Expectations: ParseError naming the unknown key.
        """
        doc = make_doc("type: story\nproject: p\nunknown_field: value\n")
        with pytest.raises(ParseError, match="unknown_field"):
            self.parser.parse(doc)

    def test_invalid_type_raises(self):
        """Setup: frontmatter with type set to an invalid value.
        Expectations: ParseError mentioning the invalid type.
        """
        doc = make_doc("type: banana\nproject: p\n")
        with pytest.raises(ParseError, match="banana"):
            self.parser.parse(doc)

    def test_valid_story_frontmatter(self):
        """Setup: complete story frontmatter.
        Expectations: returns metadata dict and body string.
        """
        doc = make_doc("type: story\nproject: my-project\nassignee: blake\n")
        metadata, body = self.parser.parse(doc)

        assert metadata["type"] == "story"
        assert metadata["project"] == "my-project"
        assert metadata["assignee"] == "blake"

    def test_tags_as_string(self):
        """Setup: tags provided as a comma-separated string.
        Expectations: tags parsed into a list.
        """
        doc = make_doc("type: story\nproject: p\ntags: backend, auth\n")
        metadata, _ = self.parser.parse(doc)

        assert metadata["tags"] == ["backend", "auth"]

    def test_tags_as_list(self):
        """Setup: tags provided as a YAML list.
        Expectations: tags returned as a list.
        """
        doc = make_doc("type: story\nproject: p\ntags:\n  - backend\n  - auth\n")
        metadata, _ = self.parser.parse(doc)

        assert metadata["tags"] == ["backend", "auth"]

    def test_body_returned(self):
        """Setup: document with frontmatter and body.
        Expectations: body content returned correctly.
        """
        doc = make_doc("type: story\nproject: p\n", "## My Title\n\nSome content.\n")
        _, body = self.parser.parse(doc)

        assert body == "## My Title\n\nSome content."


class TestFrontmatterParserBuildPartial:
    def setup_method(self):
        self.parser = FrontmatterParser()

    def test_builds_story(self):
        """Setup: metadata with type story.
        Expectations: returns a Story instance with correct fields.
        """
        metadata = {"type": "story", "project": "p", "tags": [], "epic": 2, "priority": "High"}
        result = self.parser.build_partial(metadata)

        assert isinstance(result, Story)
        assert result.project == "p"
        assert result.epic == 2
        assert result.priority == "High"
        assert result.subject == ""

    def test_builds_issue(self):
        """Setup: metadata with type issue.
        Expectations: returns an Issue with issue_type and severity set.
        """
        metadata = {
            "type": "issue", "project": "p", "tags": [],
            "issue_type": "Bug", "severity": "High",
        }
        result = self.parser.build_partial(metadata)

        assert isinstance(result, Issue)
        assert result.issue_type == "Bug"
        assert result.severity == "High"

    def test_builds_task(self):
        """Setup: metadata with type task and parent set.
        Expectations: returns a Task with parent set.
        """
        metadata = {"type": "task", "project": "p", "tags": [], "parent": 5}
        result = self.parser.build_partial(metadata)

        assert isinstance(result, Task)
        assert result.parent == 5

    def test_builds_epic(self):
        """Setup: metadata with type epic.
        Expectations: returns an Epic instance.
        """
        metadata = {"type": "epic", "project": "p", "tags": [], "color": "#ff0000"}
        result = self.parser.build_partial(metadata)

        assert isinstance(result, Epic)
        assert result.color == "#ff0000"

    def test_optional_fields_default_to_none(self):
        """Setup: minimal story metadata.
        Expectations: optional fields are None.
        """
        metadata = {"type": "story", "project": "p", "tags": []}
        result = self.parser.build_partial(metadata)

        assert result.assignee is None
        assert result.milestone is None
        assert result.epic is None
