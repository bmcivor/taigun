from taigun.models import Story, Issue, Task, Epic


class TestStory:
    def test_required_fields(self):
        """Setup: minimal Story with only required fields.
        Expectations: instantiates without error.
        """
        s = Story(project="my-project", subject="Do something")
        assert s.project == "my-project"
        assert s.subject == "Do something"

    def test_optional_fields_default_to_none(self):
        """Setup: minimal Story.
        Expectations: all optional fields are None or empty list.
        """
        s = Story(project="p", subject="s")
        assert s.description == ""
        assert s.epic is None
        assert s.assignee is None
        assert s.milestone is None
        assert s.tags == []
        assert s.status is None
        assert s.priority is None

    def test_all_fields_settable(self):
        """Setup: Story with all fields set.
        Expectations: all values stored correctly.
        """
        s = Story(
            project="p",
            subject="s",
            description="desc",
            epic=3,
            assignee="blake",
            milestone="Sprint 1",
            tags=["backend", "auth"],
            status="New",
            priority="High",
        )
        assert s.epic == 3
        assert s.tags == ["backend", "auth"]
        assert s.priority == "High"


class TestIssue:
    def test_required_fields(self):
        """Setup: minimal Issue.
        Expectations: instantiates without error.
        """
        i = Issue(project="p", subject="s")
        assert i.project == "p"
        assert i.subject == "s"

    def test_issue_specific_fields(self):
        """Setup: Issue with issue_type and severity set.
        Expectations: fields stored correctly.
        """
        i = Issue(project="p", subject="s", issue_type="Bug", severity="High")
        assert i.issue_type == "Bug"
        assert i.severity == "High"

    def test_optional_fields_default_to_none(self):
        """Setup: minimal Issue.
        Expectations: all optional fields are None or empty list.
        """
        i = Issue(project="p", subject="s")
        assert i.issue_type is None
        assert i.severity is None
        assert i.assignee is None
        assert i.milestone is None
        assert i.tags == []
        assert i.status is None
        assert i.priority is None


class TestTask:
    def test_required_fields(self):
        """Setup: minimal Task.
        Expectations: instantiates without error.
        """
        t = Task(project="p", subject="s")
        assert t.project == "p"
        assert t.subject == "s"

    def test_parent_field(self):
        """Setup: Task with parent story ref set.
        Expectations: parent stored correctly.
        """
        t = Task(project="p", subject="s", parent=7)
        assert t.parent == 7

    def test_optional_fields_default_to_none(self):
        """Setup: minimal Task.
        Expectations: all optional fields are None or empty list.
        """
        t = Task(project="p", subject="s")
        assert t.parent is None
        assert t.epic is None
        assert t.assignee is None
        assert t.milestone is None
        assert t.tags == []
        assert t.status is None


class TestEpic:
    def test_required_fields(self):
        """Setup: minimal Epic.
        Expectations: instantiates without error.
        """
        e = Epic(project="p", subject="s")
        assert e.project == "p"
        assert e.subject == "s"

    def test_optional_fields_default_to_none(self):
        """Setup: minimal Epic.
        Expectations: all optional fields are None or empty list.
        """
        e = Epic(project="p", subject="s")
        assert e.description == ""
        assert e.assignee is None
        assert e.tags == []
        assert e.status is None
        assert e.color is None

    def test_no_issue_type_or_severity(self):
        """Setup: Epic instantiated.
        Expectations: Epic has no issue_type or severity attributes.
        """
        e = Epic(project="p", subject="s")
        assert not hasattr(e, "issue_type")
        assert not hasattr(e, "severity")

    def test_no_parent_field(self):
        """Setup: Epic instantiated.
        Expectations: Epic has no parent attribute.
        """
        e = Epic(project="p", subject="s")
        assert not hasattr(e, "parent")
