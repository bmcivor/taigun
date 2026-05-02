## ~~17. list commands~~ (Done)

**Epic:** E5 — CLI

**As a** user
**I want** `taigun projects list`, `taigun epics list`, and `taigun statuses list`
**So that** I can look up slugs and names without going into the Taiga UI

### Acceptance criteria

- `taigun projects list` — prints `name (slug)` for every project
- `taigun epics list <project-slug>` — prints `#ref  subject` for every epic
- `taigun statuses list <project-slug>` — prints statuses grouped by type
  (story / issue / task / epic), one per line with closed status indicated
- All commands support `--profile <name>`
- Unknown project slug → clear error

### Dependencies

- 015

### Blocks

- 018

### Priority

- Medium
