---
type: story
project: taigun
status: Done
---

## 31. Fix the data-loss bugs surfaced by the audit

**As a** taigun user
**I want** every field present in the source markdown to land in Taiga
**So that** the ticket I see in the UI matches the ticket I wrote, without surprises

**Priority:** High

### Context

Follow-on to 030. The audit produces a list of fields/sections that don't land; this ticket fixes them. Likely candidates based on early observation:

- The As a / I want / So that block is dropped from descriptions
- Tags array may not propagate (frontmatter `tags: foo, bar` → Taiga's `tags` column)
- Possibly priority not landing as the priority FK
- Possibly other body sections (Context, Scope boundary, Failure modes) not being included

Each is its own one-line bug — typically a missing field in a writer's INSERT or a parser section that's matched but discarded.

### Acceptance criteria

- Every bug in 030's audit is fixed
- A second audit run (re-push the same source ticket to a fresh project) shows everything landing correctly
- Unit tests added covering the parsing/writing of each affected field
- All existing 180+ tests still pass

### Dependencies

- 030 (need to know what's broken)

### Blocks

- E9 (no point implementing update if push itself is lossy)
