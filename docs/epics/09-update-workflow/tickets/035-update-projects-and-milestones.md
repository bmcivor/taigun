---
type: story
project: taigun
---

## 35. Update support for projects and milestones

**As a** taigun user
**I want** the same update workflow to apply to projects and milestones, not just ticket types
**So that** every entity taigun creates can be edited via its source and re-pushed, with no entity-type left as the special case that needs manual UI edits

**Priority:** Low (less common edit case than tickets — name a project and you rarely rename, set sprint dates and you rarely shuffle them)

### Context

034 handles the four ticket types (story/task/issue/epic). This ticket extends update support to:

- **Projects** (created via `taigun projects create` — needs an update path so name, description, activated modules, etc. can be edited)
- **Milestones** (once 028 lands with `MilestoneWriter` — needs update for name, dates, closed state)

The mechanism is the same — sidecar lookup, diff-then-update — but the field shapes differ:

- Projects have module-activation booleans, default-status FKs, permissions arrays — different mutability rules than tickets
- Milestones have date fields and a closed boolean — date moves are common, closed flips are common
- Both have child relationships that need to be considered for removal semantics (deleting a milestone with stories attached — what happens?)

### Acceptance criteria

- `ProjectCreator` gains an `update` method (or a sibling `ProjectUpdater`) — matches the pattern from 034
- `MilestoneWriter` gains the same — assumes 028 lands so the writer exists
- Sidecar (033) extended to track projects + milestones, or a separate sidecar — decide and document
- Mutability rules for projects + milestones added to the ADR (032 or a follow-on ADR — decide)
- End-to-end test: edit a project's name and module activation, re-push, confirm change in DB / UI
- End-to-end test: edit a milestone's date range and closed flag, re-push, confirm change
- All existing tests still pass

### Dependencies

- 028 (MilestoneWriter must exist first)
- 034 (ticket update pattern is the template this follows)
