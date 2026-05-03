import json
from unittest.mock import MagicMock

import pytest

from taigun.db.project import ProjectCreator, ProjectExistsError
from taigun.exceptions import ResolveError


def make_resolver(user_id: int = 5):
    mock_resolver = MagicMock()
    mock_resolver.resolve_user.return_value = user_id
    return mock_resolver


def make_template_row(template_id: int = 1):
    """Returns the tuple shape the SELECT in _load_default_template expects."""
    us_statuses = [
        {"name": "New", "slug": "new", "order": 1, "is_closed": False, "color": "#aaaaaa"},
        {"name": "Done", "slug": "done", "order": 2, "is_closed": True, "color": "#bbbbbb"},
    ]
    task_statuses = [{"name": "New", "slug": "new", "order": 1, "is_closed": False}]
    issue_statuses = [{"name": "New", "slug": "new", "order": 1, "is_closed": False}]
    epic_statuses = [{"name": "New", "slug": "new", "order": 1, "is_closed": False}]
    priorities = [{"name": "Normal", "color": "#888888", "order": 1}]
    severities = [{"name": "Normal", "color": "#888888", "order": 1}]
    issue_types = [{"name": "Bug", "color": "#888888", "order": 1}]
    roles = [{"name": "Admin", "slug": "admin", "order": 1, "computable": True}]
    default_options = {
        "us_status": "New",
        "task_status": "New",
        "issue_status": "New",
        "epic_status": "New",
        "priority": "Normal",
        "severity": "Normal",
        "issue_type": "Bug",
    }
    return (
        template_id,
        json.dumps(us_statuses),
        json.dumps(task_statuses),
        json.dumps(issue_statuses),
        json.dumps(epic_statuses),
        json.dumps(priorities),
        json.dumps(severities),
        json.dumps(issue_types),
        json.dumps(roles),
        json.dumps(default_options),
    )


def make_mock_conn(slug_exists: bool = False, template_present: bool = True, role_exists: bool = False):
    """Build a mock connection that returns a sensible sequence of fetchone results."""
    cursor = MagicMock()
    sequence = []

    sequence.append((1,) if slug_exists else None)

    if template_present:
        sequence.append(make_template_row())
    else:
        sequence.append(None)

    sequence.append((101,))

    for _ in range(7):
        sequence.append((999,))

    sequence.append((42,) if role_exists else None)
    if not role_exists:
        sequence.append((42,))

    cursor.fetchone.side_effect = sequence
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    return conn, cursor


class TestProjectCreator:
    @pytest.fixture
    def resolver(self):
        return make_resolver()

    def test_returns_project_id_and_slug(self, resolver):
        """Setup: slug does not exist; default template present.
        Expectations: create returns (101, 'my-project').
        """
        conn, _ = make_mock_conn()
        creator = ProjectCreator(conn, resolver)

        result = creator.create("My Project", "my-project", "admin")

        assert result == (101, "my-project")

    def test_raises_project_exists_when_slug_already_present(self, resolver):
        """Setup: slug already present in projects_project.
        Expectations: ProjectExistsError raised with the slug in the message.
        """
        conn, _ = make_mock_conn(slug_exists=True)
        creator = ProjectCreator(conn, resolver)

        with pytest.raises(ProjectExistsError) as exc_info:
            creator.create("My Project", "my-project", "admin")

        assert "my-project" in str(exc_info.value)

    def test_raises_resolve_error_when_no_template(self, resolver):
        """Setup: no rows in projects_projecttemplate.
        Expectations: ResolveError raised.
        """
        conn, _ = make_mock_conn(template_present=False)
        creator = ProjectCreator(conn, resolver)

        with pytest.raises(ResolveError):
            creator.create("My Project", "my-project", "admin")

    def test_resolves_acting_user(self, resolver):
        """Setup: create called with acting_user 'admin'.
        Expectations: resolve_user called once with 'admin'.
        """
        conn, _ = make_mock_conn()
        creator = ProjectCreator(conn, resolver)

        creator.create("My Project", "my-project", "admin")

        resolver.resolve_user.assert_called_once_with("admin")

    def test_inserts_project_with_owner_and_template(self, resolver):
        """Setup: standard create.
        Expectations: INSERT INTO projects_project params include name, slug, owner_id, template_id.
        """
        conn, cursor = make_mock_conn()
        creator = ProjectCreator(conn, resolver)

        creator.create("My Project", "my-project", "admin")

        insert_calls = [
            call for call in cursor.execute.call_args_list
            if "INSERT INTO projects_project" in call[0][0]
        ]
        assert len(insert_calls) == 1
        params = insert_calls[0][0][1]
        assert params == ("My Project", "my-project", 5, 1)

    def test_creates_ref_sequence_for_project(self, resolver):
        """Setup: standard create returning project id 101.
        Expectations: CREATE SEQUENCE references_project101 executed.
        """
        conn, cursor = make_mock_conn()
        creator = ProjectCreator(conn, resolver)

        creator.create("My Project", "my-project", "admin")

        seq_calls = [
            call for call in cursor.execute.call_args_list
            if "CREATE SEQUENCE references_project101" in call[0][0]
        ]
        assert len(seq_calls) == 1

    def test_inserts_owner_membership_as_admin(self, resolver):
        """Setup: standard create.
        Expectations: INSERT INTO projects_membership executed with is_admin true.
        """
        conn, cursor = make_mock_conn()
        creator = ProjectCreator(conn, resolver)

        creator.create("My Project", "my-project", "admin")

        membership_calls = [
            call for call in cursor.execute.call_args_list
            if "INSERT INTO projects_membership" in call[0][0]
        ]
        assert len(membership_calls) == 1

    def test_materialises_statuses_for_all_four_types(self, resolver):
        """Setup: template has one status entry per type (us, task, issue, epic).
        Expectations: one INSERT into each of the four status tables.
        """
        conn, cursor = make_mock_conn()
        creator = ProjectCreator(conn, resolver)

        creator.create("My Project", "my-project", "admin")

        for table in (
            "projects_userstorystatus",
            "projects_taskstatus",
            "projects_issuestatus",
            "projects_epicstatus",
        ):
            inserts = [
                call for call in cursor.execute.call_args_list
                if f"INSERT INTO {table}" in call[0][0]
            ]
            assert len(inserts) >= 1, f"Expected at least one INSERT INTO {table}"
