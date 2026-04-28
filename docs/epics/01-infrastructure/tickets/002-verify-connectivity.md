## 2. Verify DB connectivity from dev machine

**Epic:** E1 — Infrastructure & connectivity

**As a** taigun developer
**I want** to confirm direct Postgres access works from my dev machine over Tailscale
**So that** the connectivity foundation is confirmed before DB code is written

### Acceptance criteria

- `psql` connects from dev machine using the Tailscale IP, port 5432, taiga credentials
- Can run `SELECT slug FROM projects_project;` and see results
- Can run `SELECT id, name FROM projects_priority WHERE project_id = 1;` without error
- Result recorded — confirms which project IDs exist for use in E4 testing

### Dependencies

- 001

### Blocks

- 008 (DB connection module)

### Priority

- High
