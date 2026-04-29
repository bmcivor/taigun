import frontmatter
from typing import Union

from taigun.exceptions import ParseError
from taigun.models import Story, Issue, Task, Epic


KNOWN_FRONTMATTER_KEYS = {
    "type", "project", "epic", "assignee", "milestone",
    "tags", "status", "parent", "issue_type", "severity",
}

TICKET_TYPES = {"story", "issue", "task", "epic"}


def _parse_tags(value) -> list[str]:
    """Parse tags from either a comma-separated string or a list.

    Args:
        value: Either a string like "backend, auth" or a list like ["backend", "auth"].

    Returns:
        List of stripped tag strings.
    """
    if isinstance(value, list):
        return [str(t).strip() for t in value]
    return [t.strip() for t in str(value).split(",") if t.strip()]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a markdown string into frontmatter fields and body text.

    Args:
        text: Raw markdown file content.

    Returns:
        A tuple of (frontmatter dict, body string).

    Raises:
        ParseError: If required fields are missing or unknown keys are present.
    """
    post = frontmatter.loads(text)
    metadata = dict(post.metadata)
    body = post.content

    unknown = set(metadata.keys()) - KNOWN_FRONTMATTER_KEYS
    if unknown:
        raise ParseError(f"Unknown frontmatter fields: {', '.join(sorted(unknown))}")

    for required in ("type", "project"):
        if required not in metadata:
            raise ParseError(f"Missing required frontmatter field: '{required}'")

    ticket_type = metadata["type"]
    if ticket_type not in TICKET_TYPES:
        raise ParseError(
            f"Invalid ticket type '{ticket_type}'. Must be one of: {', '.join(sorted(TICKET_TYPES))}"
        )

    if "tags" in metadata:
        metadata["tags"] = _parse_tags(metadata["tags"])

    return metadata, body


def _build_partial(metadata: dict) -> Union[Story, Issue, Task, Epic]:
    """Construct a partial ticket dataclass from frontmatter metadata.

    Body fields (subject, description) are left at their defaults.

    Args:
        metadata: Parsed frontmatter dict.

    Returns:
        A partially populated Story, Issue, Task, or Epic dataclass.
    """
    ticket_type = metadata["type"]
    common = {
        "project": metadata["project"],
        "subject": "",
        "assignee": metadata.get("assignee"),
        "milestone": metadata.get("milestone"),
        "tags": metadata.get("tags", []),
        "status": metadata.get("status"),
    }

    match ticket_type:
        case "story":
            return Story(
                **common,
                epic=metadata.get("epic"),
                priority=metadata.get("priority"),
            )
        case "issue":
            return Issue(
                **common,
                issue_type=metadata.get("issue_type"),
                severity=metadata.get("severity"),
                priority=metadata.get("priority"),
            )
        case "task":
            return Task(
                **common,
                parent=metadata.get("parent"),
                epic=metadata.get("epic"),
            )
        case "epic":
            return Epic(
                project=metadata["project"],
                subject="",
                assignee=metadata.get("assignee"),
                tags=metadata.get("tags", []),
                status=metadata.get("status"),
                color=metadata.get("color"),
            )
