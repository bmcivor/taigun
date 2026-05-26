---
type: story
project: taigun
---

## 32. Design update workflow (ADR)

**As a** taigun developer
**I want** the update-workflow design committed as an ADR before any code is written
**So that** the semantics around ticket identification, mutability, and error handling are decided once and visible, not invented per-PR

### Context

The interesting decisions are not the SQL — they're the workflow shape. Things to resolve in this ticket, not in implementation:

- **Identification**: how does the second push know it's updating ticket #42 vs creating a new one? Options:
  - `taigun_ref` frontmatter field, written back by push on first run
  - `(project, slug-derived-from-title)` natural key
  - Content-addressed (hash the body — but title edits would orphan)
- **Mutability**: which fields can change? Title and description obviously. Status? Priority? Milestone? Type? Project itself?
- **Removal semantics**: if a frontmatter field is present on push 1 but absent on push 2, do we (a) clear that field, (b) leave it as-is, (c) error?
- **Conflict semantics**: if Taiga has been edited in the UI since the last push, do we (a) overwrite blindly, (b) detect via `modified_date` and refuse, (c) detect and prompt?
- **Idempotency**: re-pushing an unchanged file should be a no-op, not a 200-row update

### Acceptance criteria

- ADR file at `docs/decisions/ADR-NNN-update-workflow.md`
- Covers each decision above with: chosen option, rejected options, rationale
- References the existing ADRs for taigun's design philosophy (direct DB writes, etc.) where relevant
- Reviewed by B before any of 033/034 starts

### Dependencies

- E8 031 (push needs to be lossless first, or the ADR's idempotency claims are nonsense)

### Blocks

- 033, 034

### Priority

- High (gates all the update code)
