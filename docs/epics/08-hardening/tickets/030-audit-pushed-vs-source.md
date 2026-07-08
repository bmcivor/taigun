---
type: story
project: taigun
status: Done
---

## 30. Audit what fields actually land on push, vs what was in the source markdown

**As a** taigun user
**I want** an explicit field-by-field diff between source markdown and pushed Taiga ticket
**So that** the silent data-loss bugs we hit in v1.0 dog-fooding are enumerated, not discovered one at a time when something looks wrong in the UI

**Priority:** High (gates all the update-workflow work — no point shipping update if pushes are lossy)

### Context

In dog-fooding vertex-play (v1.0), at least one body section (the As a / I want / So that block) does not appear to land in the Taiga description as expected. Looking at the UI for a pushed story, the description starts at "Acceptance criteria" with no user-story preamble above it. There may be other fields silently dropped (tags, priority, milestone, etc.) that nobody's noticed yet because nothing visibly broken.

This is a diagnostic ticket — no fixes. The goal is to know what's actually wrong before deciding how to fix it.

### Acceptance criteria

- Pick one well-populated source ticket (e.g. `vertex-play/docs/epics/01-lab-integration/tickets/001-verify-lab-prerequisites.md`)
- Compare side-by-side what was in the markdown vs what landed in Taiga (DB row + UI rendering)
- For each frontmatter field, document: landed correctly / not landed / wrong value
- For each body section, document the same
- Produce a checklist of bugs found — written to `docs/dog-food-audit.md` or as the body of this ticket's resolution
- No code changes in this ticket — 031 handles the fixes

### Dependencies

- v1.0 released

### Blocks

- 031
