"""Shared helpers for the writer ``update()`` methods.

Each helper enforces one of the ADR-004 semantics so the writers stay
focused on their INSERT/UPDATE shape. Callers pass the exception class
they want raised so ticket / milestone / project entities can each carry
their own error types.
"""

import datetime
from typing import Type

from taigun.exceptions import FieldClearedError, TicketConflictError


def parse_taiga_timestamp(value: str) -> datetime.datetime:
    """Parse an ISO-8601 timestamp coming out of the sidecar or Taiga."""
    text = value.replace("Z", "+00:00") if isinstance(value, str) else str(value)
    return datetime.datetime.fromisoformat(text)


def check_taiga_conflict(
    taiga_modified_date: datetime.datetime,
    sidecar_last_pushed_at: datetime.datetime,
    conflict_exception: Type[Exception] = TicketConflictError,
) -> None:
    """Raise ``conflict_exception`` if Taiga's row was edited after the
    last push recorded in the sidecar.

    ``conflict_exception`` must accept ``(message, taiga_modified_date=...)``
    like ``TicketConflictError`` — the milestone variant follows the same
    shape.

    Millisecond drift between the two clocks is tolerated (1 second grace).
    """
    if taiga_modified_date is None:
        return

    taiga = taiga_modified_date
    if taiga.tzinfo is None:
        taiga = taiga.replace(tzinfo=datetime.timezone.utc)

    sidecar = sidecar_last_pushed_at
    if sidecar.tzinfo is None:
        sidecar = sidecar.replace(tzinfo=datetime.timezone.utc)

    if taiga - sidecar > datetime.timedelta(seconds=1):
        raise conflict_exception(
            f"row was modified at {taiga.isoformat()} "
            f"(last push at {sidecar.isoformat()})",
            taiga_modified_date=taiga.isoformat(),
        )


def check_field_cleared(
    field_name: str,
    metadata_keys: set,
    current_db_value,
    cleared_exception: Type[Exception] = FieldClearedError,
) -> None:
    """Raise ``cleared_exception`` if a frontmatter field is now absent but
    the current DB row has a non-null / non-empty value for it.

    Clearing a field requires an explicit ``field: null`` in the source to
    keep accidental deletions loud.
    """
    if field_name in metadata_keys:
        return

    if current_db_value in (None, "", 0, [], (), {}):
        return

    raise cleared_exception(
        f"'{field_name}' was previously set but is now absent from the "
        f"source. Add `{field_name}: null` to explicitly clear it."
    )
