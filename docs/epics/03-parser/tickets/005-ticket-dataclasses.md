## ~~5. Ticket dataclasses~~ (Done)

**Epic:** E3 — Markdown parser

**As a** developer
**I want** typed dataclasses for Story, Issue, Task, and Epic
**So that** the parser and writer share a single contract with no ambiguity

### Acceptance criteria

- `models.py` defines dataclasses: `Story`, `Issue`, `Task`, `Epic`
- All settable fields present on each type, matching the field list in `docs/ticket-format.md`
- Optional fields typed as `Optional[T]` with `None` defaults
- `subject` and `project` are required (non-optional) on all types
- `Issue` includes `issue_type` and `severity` fields not present on other types
- `Task` includes `parent` field (parent story ref) not present on other types
- No logic in models — pure data containers

### Dependencies

- 003

### Blocks

- 006, 007, 009, 011, 012, 013, 014

### Priority

- High
