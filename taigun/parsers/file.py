from pathlib import Path
from typing import Union

from taigun.exceptions import ParseError
from taigun.models import Story, Issue, Task, Epic, Milestone
from taigun.parsers.frontmatter import FrontmatterParser
from taigun.parsers.body import BodyParser


class FileParser:
    """Parses a markdown ticket file into a fully populated dataclass.

    Composes FrontmatterParser and BodyParser into a single entry point.
    """

    def __init__(self) -> None:
        self._frontmatter = FrontmatterParser()
        self._body = BodyParser()

    def parse(self, path: Union[str, Path]) -> Union[Story, Issue, Task, Epic, Milestone]:
        """Read a markdown ticket file and return a fully populated dataclass.

        Priority (either as a ``priority:`` frontmatter field or a
        ``### Priority`` body section) is only valid on issue tickets — Taiga's
        schema has no priority column for stories, tasks, or epics. Priority on
        any other ticket type raises ParseError.

        Milestones have no description column in Taiga's schema; a milestone
        file must contain only the ``## Title`` heading in its body. Any
        additional content raises ParseError.

        Args:
            path: Path to the markdown ticket file.

        Returns:
            A fully populated Story, Issue, Task, Epic, or Milestone dataclass.

        Raises:
            ParseError: If the file cannot be parsed, if priority appears on
                a story/task/epic, or if a milestone body has content beyond
                the title.
        """
        text = Path(path).read_text()

        metadata, body = self._frontmatter.parse(text)
        subject, description, body_priority = self._body.parse(body)

        fm_priority = metadata.get("priority")
        if (body_priority is not None or fm_priority is not None) and metadata["type"] != "issue":
            raise ParseError(
                f"Priority is only supported on issue tickets. "
                f"This is a {metadata['type']}; remove the `priority:` frontmatter "
                f"field and any `### Priority` section."
            )

        ticket = self._frontmatter.build_partial(metadata)
        ticket.subject = subject

        if isinstance(ticket, Milestone):
            if description:
                raise ParseError(
                    "Milestone body must contain only the `## Title` heading; "
                    "Taiga's schema has no description column for milestones. "
                    "Remove the extra content."
                )
            return ticket

        ticket.description = description

        if body_priority is not None:
            ticket.priority = body_priority

        return ticket
