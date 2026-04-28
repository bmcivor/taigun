## 13. Task writer

**Epic:** E4 — DB layer

**As a** developer
**I want** db.py to insert tasks with all supported fields
**So that** task tickets pushed via the CLI land correctly in Taiga

### Acceptance criteria

- `insert_task(conn, task: Task, resolver)` in `db.py`
- Inserts into `tasks_task` with:
  - `subject`, `description`, `project_id`, `status_id`, `owner_id`, `ref`,
    `created_date`, `modified_date`, `version = 1`
  - `user_story_id` if `parent` ref is set (resolved via resolver)
  - `assigned_to_id` if set
  - `milestone_id` if set
  - `us_order` and `taskboard_order` set to current timestamp integer
- Ref allocated via `allocate_ref` (010)
- Entire operation runs in a single transaction
- Returns the allocated ref number

### Dependencies

- 009, 010, 005

### Blocks

- 016

### Priority

- High
