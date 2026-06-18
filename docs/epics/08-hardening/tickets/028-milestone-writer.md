---
type: story
project: taigun
---

## 28. MilestoneWriter

**As a** taigun user
**I want** to create Taiga milestones (sprints) via taigun
**So that** sprint setup is part of the same scripted workflow as tickets, and tests don't need raw SQL to fake one

**Priority:** Low (current workflow — create milestones in Taiga UI — is acceptable for solo use)

### Context

taigun has no `MilestoneWriter`. Stories, tasks, and issues can reference a milestone
by name (resolved via `Resolver.resolve_milestone`), but the milestone itself has to
exist before the push. Currently that means going into the Taiga UI to create it.

This also leaks into the test suite: `tests/factories.py::make_milestone` uses raw SQL
to insert a milestone row, which violates the "tests use app code, no raw SQL" rule
that the factories module's docstring claims. It's a documented exception, but it
should not be permanent.

A `MilestoneWriter` parallels the existing ticket writers — INSERT into
`milestones_milestone`, fill the NOT NULL columns we identified
(name, slug, estimated_start, estimated_finish, created_date, modified_date, closed,
"order", project_id), allocate ownership via `acting_user`.

A new CLI command (`taigun milestones create`, probably under `taigun milestones …`
to match the existing `taigun projects …` and `taigun statuses …` pattern) wires it
to the user.

### Acceptance criteria

- New `taigun/db/milestone.py` with a `MilestoneWriter` class — follows the same
  shape as the existing writers (constructor takes `conn`, `resolver`; method takes
  a `Milestone` model and `acting_user`, returns the inserted id)
- New `Milestone` dataclass in `taigun/models.py` with fields:
  `project` (required), `name` (required), `estimated_start`, `estimated_finish`,
  `closed` (default False), `order` (default 1)
- Frontmatter parser updated to accept `type: milestone` (and any
  milestone-specific frontmatter fields like `estimated_start`, `estimated_finish`)
- New CLI command `taigun milestones create <project-slug> <name>` (or push-via-frontmatter
  — pick one and document)
- `tests/factories.py::make_milestone` rewritten to use `MilestoneWriter`, the raw
  SQL exception note in the module docstring removed
- Tests added for `MilestoneWriter` matching the coverage pattern of other writer
  tests
- All 180 existing tests still pass

### Dependencies

- v1.0 released
