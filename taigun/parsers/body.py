import re
from typing import Optional

from taigun.exceptions import ParseError


class BodyParser:
    """Parses the markdown body of a ticket file into its component fields.

    Extracts the subject from the ``## Title`` heading, strips the
    ``### Priority`` section into a separate field, and assembles all
    remaining ``###`` sections into the description.
    """

    def parse(self, body: str) -> tuple[str, str, Optional[str]]:
        """Parse the markdown body into subject, description, and optional priority.

        The first ``## Heading`` becomes the subject. ``### Priority`` is extracted
        as the priority value and excluded from the description. All other ``###``
        sections are assembled into the description in order, headings preserved.

        Args:
            body: Markdown body text after the frontmatter block.

        Returns:
            A tuple of (subject, description, priority). Priority is None if no
            ``### Priority`` section is present.

        Raises:
            ParseError: If no ``## Title`` heading is found in the body.
        """
        title_match = re.search(r"^## (.+)$", body, re.MULTILINE)

        if title_match is None:
            raise ParseError("Body is missing a ## Title heading")
        subject = title_match.group(1).strip()

        priority: Optional[str] = None
        description_parts: list[str] = []

        for section in re.split(r"^### ", body, flags=re.MULTILINE)[1:]:
            heading, _, content = section.partition("\n")
            heading = heading.strip()
            content = content.strip()
            if heading.lower() == "priority":
                priority = content or None
            else:
                description_parts.append(f"### {heading}\n{content}")

        description = "\n\n".join(description_parts)

        return subject, description, priority
