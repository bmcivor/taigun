from pathlib import Path
from typing import Union

from taigun.models import Story, Issue, Task, Epic
from taigun.parsers.frontmatter import FrontmatterParser
from taigun.parsers.body import BodyParser


class FileParser:
    """Parses a markdown ticket file into a fully populated dataclass.

    Composes FrontmatterParser and BodyParser into a single entry point.
    """

    def __init__(self) -> None:
        self._frontmatter = FrontmatterParser()
        self._body = BodyParser()

    def parse(self, path: Union[str, Path]) -> Union[Story, Issue, Task, Epic]:
        """Read a markdown ticket file and return a fully populated dataclass.

        If priority appears in both frontmatter and a ``### Priority`` body
        section, the body value takes precedence.

        Args:
            path: Path to the markdown ticket file.

        Returns:
            A fully populated Story, Issue, Task, or Epic dataclass.

        Raises:
            ParseError: If the file cannot be parsed.
        """
        text = Path(path).read_text()

        metadata, body = self._frontmatter.parse(text)
        ticket = self._frontmatter.build_partial(metadata)

        subject, description, priority = self._body.parse(body)
        ticket.subject = subject
        ticket.description = description

        if priority is not None and hasattr(ticket, "priority"):
            ticket.priority = priority

        return ticket
