---
type: story
project: taigun
---

## 34. Implement taigun update / upsert

**As a** taigun user
**I want** to re-push an edited markdown file and have Taiga reflect the changes
**So that** docs and tickets stay in sync without manually editing both

### Context

Builds on 032 (semantics) and 033 (round-trip). The actual implementation.

Shape of the command depends on what 032 decides. Two reasonable shapes:

- **Separate command**: `taigun update <files>` — explicit, no surprises. `taigun push` stays insert-only.
- **Upsert push**: `taigun push <files>` checks `taigun_ref` and decides insert-vs-update per file. One command, less explicit.

Implementation per ticket type (story/task/issue/epic) is symmetric — each writer needs an `update` method alongside `write`, doing `UPDATE <table> SET ...` on the row matched by ref.

Field-mutability rules from 032 drive what gets included in the UPDATE clause.

### Acceptance criteria

- New writer `update` method per type (story/task/issue/epic), updating only the fields the ADR (032) says are mutable
- CLI surface matches the ADR's decision (`taigun update` vs upsert on `push`)
- Conflict detection per the ADR — refusing or warning when Taiga's `modified_date` is newer than the last push
- End-to-end test: push a story, edit a field in the markdown, re-push, assert the field updates in the DB
- Field-removal semantics implemented per the ADR (clear vs leave vs error)
- Idempotency: re-pushing unchanged content is a no-op (no SQL UPDATE if no fields changed)
- All existing tests still pass
- Real-Taiga dog-food: edit a ticket previously pushed to the lab, re-push, confirm in the UI

### Dependencies

- 032 (semantics)
- 033 (refs in frontmatter)

### Priority

- Medium
