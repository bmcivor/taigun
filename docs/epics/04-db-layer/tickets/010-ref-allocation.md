## 10. Ref allocation

**Epic:** E4 — DB layer

**As a** developer
**I want** ref allocation handled as a shared utility in db.py
**So that** all writers get a correct ref number and references_reference row without
duplicating the logic

### Context

Taiga uses per-project Postgres sequences (`references_project1`, `references_project2`,
etc. where the number is the project ID) to generate human-visible ticket numbers.
Each ticket also needs a corresponding row in `references_reference` linking the ref
to the object via Django's content type system.

Without a correct ref, tickets appear on the board with no `#` number and filtering
breaks.

### Acceptance criteria

- `allocate_ref(conn, project_id, object_id, content_type_id)` in `db.py`:
  - Calls `SELECT nextval('references_project{project_id}')` to get the next ref
  - Inserts into `references_reference` with `(ref, object_id, content_type_id)`
  - Must be called within the same transaction as the ticket insert
  - Returns the allocated ref value
- If the sequence for the given project does not exist → raises a clear error

### Dependencies

- 008, 009

### Blocks

- 011, 012, 013, 014

### Priority

- High
