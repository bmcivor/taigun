---
type: story
project: taigun
assignee: bmcivor
---

## 37. Status resolver fails hard on unknown status name

**As a** taigun user pushing a ticket whose frontmatter names a status the
project doesn't have
**I want** the push to warn and fall back to the project's default status,
same as priority does
**So that** one file with a status typo (or a taigun-lifecycle keyword like
`Postponed`) doesn't fail the whole batch

### Context

Found by the 025 dog-food pass on 2026-07-14. Pushing 45 files, 44 succeeded
and one errored:

```
✗ 029-api-smoke-test.md: Status 'Postponed' not found for project 8
```

`029-api-smoke-test.md` has `status: Postponed` in its frontmatter (added as
part of the E9 close-out). Taiga's default template has no "Postponed"
status, so `resolve_status` raises. Compare `resolve_priority` in the same
file: unknown name → warn + fall back to the project default. Same argument
applies to statuses, and the mismatch turned a single-file input issue into
a batch failure.

### Proposed fix

Make `resolve_status` symmetric with `resolve_priority` in
`taigun/resolver.py`:

- Case-insensitive lookup, same as today
- If ``name`` is None or no match is found, return the ticket-type's project
  default (`default_us_status_id` / `default_task_status_id` / etc.)
- Log a warning only when a name was given but not found

### Acceptance criteria

- `resolve_status` with an unknown status name returns the project's default
  status ID for that ticket type and logs a warning
- `resolve_status` with an unset name returns the default with no warning
- Push of a file with `status: <not-in-project>` completes with the default
  status applied and a warning on stderr, instead of failing
- Regression tests in `tests/test_resolver.py` covering both branches (unknown
  name → warn + default, None → default without warning)

### Dependencies

- 009 (introduced `resolve_status`)
