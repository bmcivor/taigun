from pathlib import Path
from typing import Union

from taigun.models import Story, Issue, Task, Epic
from taigun.parsers.frontmatter import FrontmatterParser
from taigun.parsers.body import BodyParser


def parse_file(path: Union[str, Path]) -> Union[Story, Issue, Task, Epic]:
    """Read a markdown ticket file and return a fully populated dataclass.

    Combines frontmatter and body parsing. If priority appears in both
    frontmatter and a ``### Priority`` body section, the body value takes
    precedence.

    Args:
        path: Path to the markdown ticket file.

    Returns:
        A fully populated Story, Issue, Task, or Epic dataclass.

    Raises:
        ParseError: If the file cannot be parsed.
    """
    text = Path(path).read_text()

    fp = FrontmatterParser()
    metadata, body = fp.parse(text)
    ticket = fp.build_partial(metadata)

    subject, description, priority = BodyParser().parse(body)
    ticket.subject = subject
    ticket.description = description
    if priority is not None and hasattr(ticket, "priority"):
        ticket.priority = priority

    return ticket
