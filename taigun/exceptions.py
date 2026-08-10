class TaigunError(Exception):
    """Base for every taigun-raised exception.

    Library code should raise a ``TaigunError`` subclass instead of
    ``SystemExit`` so the CLI layer can catch it, keep the sidecar
    save-on-exit invariant intact, and translate it to a clean exit
    without a traceback.
    """


class ParseError(TaigunError):
    pass


class ResolveError(TaigunError):
    pass


class ConfigError(TaigunError):
    """Raised when the config file is missing, the requested profile is
    absent, or the profile has missing required fields."""


class DatabaseConnectionError(TaigunError):
    """Raised when opening the PostgreSQL connection fails."""


class RefAllocationError(TaigunError):
    """Raised when the per-project ref sequence needed to allocate a new
    ref number does not exist."""


class TicketMissingError(TaigunError):
    """Raised when an update targets a ref that no longer exists in Taiga."""


class TicketConflictError(TaigunError):
    """Raised when Taiga's row was modified after the last push recorded in
    the sidecar.

    The caller is expected to prompt the user; on confirmation it can call
    ``update(..., ignore_conflict=True)`` to overwrite.
    """

    def __init__(self, message: str, taiga_modified_date: str) -> None:
        super().__init__(message)
        self.taiga_modified_date = taiga_modified_date


class IdentityChangeError(TaigunError):
    """Raised when a re-push tries to change an identity field (project or
    type), which taigun refuses on principle — that's not an edit, that's a
    different ticket.
    """


class FieldClearedError(TaigunError):
    """Raised when a re-push omits a frontmatter field that had a value on
    the previous push. Per ADR-004 clearing requires an explicit ``field:
    null`` so we don't lose data to a typo or an accidental deletion.
    """


class MilestoneMissingError(TaigunError):
    """Raised when a milestone update targets a milestone that no longer
    exists in Taiga."""


class MilestoneConflictError(TaigunError):
    """Raised when Taiga's milestone row was modified after the last push
    recorded in the sidecar.
    """

    def __init__(self, message: str, taiga_modified_date: str) -> None:
        super().__init__(message)
        self.taiga_modified_date = taiga_modified_date


class ProjectMissingError(TaigunError):
    """Raised when ``taigun projects update`` targets a slug that doesn't
    exist in Taiga."""
