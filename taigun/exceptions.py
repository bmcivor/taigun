class ParseError(Exception):
    pass


class ResolveError(Exception):
    pass


class TicketMissingError(Exception):
    """Raised when an update targets a ref that no longer exists in Taiga."""


class TicketConflictError(Exception):
    """Raised when Taiga's row was modified after the last push recorded in
    the sidecar.

    The caller is expected to prompt the user; on confirmation it can call
    ``update(..., ignore_conflict=True)`` to overwrite.
    """

    def __init__(self, message: str, taiga_modified_date: str) -> None:
        super().__init__(message)
        self.taiga_modified_date = taiga_modified_date


class IdentityChangeError(Exception):
    """Raised when a re-push tries to change an identity field (project or
    type), which taigun refuses on principle — that's not an edit, that's a
    different ticket.
    """


class FieldClearedError(Exception):
    """Raised when a re-push omits a frontmatter field that had a value on
    the previous push. Per ADR-004 clearing requires an explicit ``field:
    null`` so we don't lose data to a typo or an accidental deletion.
    """


class MilestoneMissingError(Exception):
    """Raised when a milestone update targets a milestone that no longer
    exists in Taiga."""


class MilestoneConflictError(Exception):
    """Raised when Taiga's milestone row was modified after the last push
    recorded in the sidecar.
    """

    def __init__(self, message: str, taiga_modified_date: str) -> None:
        super().__init__(message)
        self.taiga_modified_date = taiga_modified_date


class ProjectMissingError(Exception):
    """Raised when ``taigun projects update`` targets a slug that doesn't
    exist in Taiga."""
