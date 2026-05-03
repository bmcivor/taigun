## 20. projects create command

**Epic:** E5 — CLI

**As a** user
**I want** `taigun projects create <name> <slug>` to create a new Taiga project from the command line
**So that** I can bootstrap a project without going into the Taiga UI before pushing tickets

### Acceptance criteria

- `taigun projects create <name> <slug>` creates the project row in `projects_project`
- Initialises the per-project ref sequence (`references_project<N>`)
- Creates default statuses for story, task, issue, epic (matching Taiga's defaults)
- Creates default priorities, severities, issue types
- Adds the configured `acting_user` as project owner with admin role
- Returns the new project ID and slug on success
- `--profile <name>` flag supported
- Project slug already exists → clear error, no partial state left in the DB

### Context

Taiga's Django app normally handles all of this initialisation via signals on project
creation. Because taigun bypasses signals, project creation must replicate the setup
explicitly so that subsequent ticket pushes against the new project work end-to-end.

This is the unblocker for using taigun against a fresh Taiga instance without first
having to go into the Taiga UI to create the project.

### Dependencies

- 008, 009

### Blocks

- 019

### Priority

- Medium
