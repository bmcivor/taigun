## ~~9. Resolver~~ (Done)

**Epic:** E4 — DB layer

**As a** developer
**I want** resolver.py to look up FK IDs for all referenced entities
**So that** writers contain only insert logic and no lookup logic

### Acceptance criteria

- `resolver.py` implements:
  - `resolve_project(conn, slug)` → `project_id`
  - `resolve_user(conn, username)` → `user_id`
  - `resolve_status(conn, project_id, name, ticket_type)` → `status_id`
  - `resolve_priority(conn, project_id, name)` → `priority_id`
  - `resolve_issue_type(conn, project_id, name)` → `type_id`
  - `resolve_severity(conn, project_id, name)` → `severity_id`
  - `resolve_epic(conn, project_id, ref)` → `epic_id`
  - `resolve_content_type(conn, app_label, model)` → `content_type_id`
- All resolvers raise `ResolveError` on no match, naming what was not found
- Priority matching is case-insensitive; falls back to project default if no match
  and logs a warning
- Content type IDs looked up once per session and cached in a module-level dict

### Dependencies

- 008, 005

### Blocks

- 010, 011, 012, 013, 014

### Priority

- High
