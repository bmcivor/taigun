## 14. Epic writer

**Epic:** E4 — DB layer

**As a** developer
**I want** db.py to insert epics with all supported fields
**So that** epic tickets pushed via the CLI land correctly in Taiga

### Acceptance criteria

- `insert_epic(conn, epic: Epic, resolver)` in `db.py`
- Inserts into `epics_epic` with:
  - `subject`, `description`, `project_id`, `status_id`, `owner_id`, `ref`,
    `created_date`, `modified_date`, `version = 1`
  - `color` defaults to a random hex colour (`#rrggbb`) if not set in frontmatter
  - `assigned_to_id` if set
  - `epics_order` set to current timestamp integer
- Ref allocated via `allocate_ref` (010)
- Entire operation runs in a single transaction
- Returns the allocated ref number

### Dependencies

- 009, 010, 005

### Blocks

- 016

### Priority

- High
