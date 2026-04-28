## 12. Issue writer

**Epic:** E4 — DB layer

**As a** developer
**I want** db.py to insert issues with all supported fields
**So that** issue tickets pushed via the CLI land correctly in Taiga

### Acceptance criteria

- `insert_issue(conn, issue: Issue, resolver)` in `db.py`
- Inserts into `issues_issue` with:
  - `subject`, `description`, `project_id`, `status_id`, `priority_id`, `type_id`,
    `severity_id`, `owner_id`, `ref`, `created_date`, `modified_date`, `version = 1`
  - `assigned_to_id` if set
  - `milestone_id` if set
- Ref allocated via `allocate_ref` (010)
- Entire operation runs in a single transaction
- Returns the allocated ref number

### Dependencies

- 009, 010, 005

### Blocks

- 016

### Priority

- High
