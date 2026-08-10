import re
from typing import Optional

from taigun.exceptions import ParseError


class BodyParser:
    """Parses the markdown body of a ticket file into its component fields.

    Extracts the subject from the ``## Title`` heading, strips the
    ``### Priority`` section into a separate field, and preserves all
    remaining body content verbatim as the description.
    """

    def parse(self, body: str) -> tuple[str, str, Optional[str]]:
        """Parse the markdown body into subject, description, and optional priority.

        The first ``## Heading`` becomes the subject. ``### Priority`` is extracted
        as the priority value and excluded from the description. Everything else
        after the title — including the As a / I want / So that block above the
        first ``###`` heading and the blank lines between headings and content —
        is preserved verbatim in the description.

        Args:
            body: Markdown body text after the frontmatter block.

        Returns:
            A tuple of (subject, description, priority). Priority is None if no
            ``### Priority`` section is present.

        Raises:
            ParseError: If no ``## Title`` heading is found in the body.
        """
        lines = body.split("\n")

        subject: Optional[str] = None
        title_idx = -1
        for i, line in enumerate(lines):
            m = re.match(r"^## (.+)$", line)
            if m:
                subject = m.group(1).strip()
                title_idx = i
                break

        if subject is None:
            raise ParseError("Body is missing a ## Title heading")

        description_lines: list[str] = []
        priority: Optional[str] = None
        in_priority_section = False

        for line in lines[title_idx + 1 :]:
            heading_match = re.match(r"^### (.+)$", line)
            if heading_match is not None:
                heading = heading_match.group(1).strip()
                if heading.lower() == "priority":
                    in_priority_section = True
                    continue
                in_priority_section = False
                description_lines.append(line)
            elif in_priority_section:
                stripped = line.strip()
                if stripped:
                    priority = re.sub(r"^[-*]\s*", "", stripped)
            else:
                description_lines.append(line)

        description = "\n".join(description_lines).strip("\n")

        return subject, description, priority
