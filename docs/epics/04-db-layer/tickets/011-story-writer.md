## ~~11. User story writer~~ (Done)

**Epic:** E4 — DB layer

**As a** developer
**I want** db.py to insert user stories with all supported fields
**So that** story tickets pushed via the CLI land correctly in Taiga

### Acceptance criteria

- `insert_story(conn, story: Story, resolver)` in `db.py`
- Inserts into `userstories_userstory` with:
  - `subject`, `description`, `project_id`, `status_id`, `priority` (via project default
    if not set), `owner_id`, `ref`, `created_date`, `modified_date`, `version = 1`
  - `milestone_id` if set
  - `assigned_to_id` if set
  - `backlog_order`, `sprint_order`, `kanban_order` set to current timestamp integer
    (Taiga convention for new items)
- If `assignee` set, inserts into `userstories_userstory_assigned_users` M2M table
- If `epic` ref set, inserts into `epics_relateduserstory`
- Ref allocated via `allocate_ref` (010)
- Entire operation runs in a single transaction
- Returns the allocated ref number

### Dependencies

- 009, 010, 005

### Blocks

- 016

### Priority

- High
