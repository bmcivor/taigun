---
type: story
project: taigun
status: Done
---

## 35. Update support for projects and milestones

**As a** taigun user
**I want** the same update workflow to apply to projects and milestones, not just ticket types
**So that** every entity taigun creates can be edited without dropping to the Taiga UI

### Context

034 handles the four ticket types (story/task/issue/epic). This ticket extends update to milestones (via the same push pipeline) and projects (via a new flag-driven CLI, since projects have no source-file representation today).

### Acceptance criteria

- `MilestoneWriter.update()` follows the 034 pattern (fetch → conflict check → UPDATE); milestones don't get a field-cleared check since owner defaults to acting_user and there's no way to tell "cleared" from "never set"
- `taigun push` routes milestone source files to the writer's update method — unchanged file is a no-op, edited file prints `↺ milestone: "<subject>" (updated)`, missing / conflict cases prompt the user the same way ticket types do
- `ProjectUpdater.update(slug, name=None, description=None)` writes only the fields that were passed
- `taigun projects update <slug> [--name] [--description]` — errors if no flags passed and errors if slug is missing
- Entity-scoped exceptions: `MilestoneMissingError`, `MilestoneConflictError`, `ProjectMissingError` — no reuse of ticket-scoped names
- All existing tests still pass

### Dependencies

- 028 (MilestoneWriter must exist first) — done
- 034 (ticket update pattern is the template this follows) — done
