# Database writes

taigun writes to Taiga's PostgreSQL schema directly, doing by hand what Taiga's
Django application would do through the ORM and its signals. The reasoning for
this approach is [ADR-001](decisions/ADR-001-direct-db-writes.md); this page
covers what actually gets written.

## Insert sequence

Each ticket insert runs in a single transaction:

1. Resolve the project slug to a `project_id`
2. Resolve the acting user to an `owner_id`
3. Resolve FK lookups per project — `status`, and for issues also `priority`,
   `severity`, and `type`
4. `INSERT` the ticket row
5. Allocate the ref: `SELECT nextval('references_project<N>')`, insert the
   corresponding `references_reference` row, and write the ref back onto the
   ticket row
6. Commit

The sidecar records the file-to-ref mapping only after the transaction commits.

!!! note "Ref sequences are non-transactional"
    Sequence advances survive rollback — this is standard PostgreSQL behaviour,
    and it is why a `--dry-run` push leaves gaps in ticket numbering (see the
    [CLI reference](../reference/cli.md)).

## Tables written per ticket type

| Type | Primary table | Secondary writes |
|---|---|---|
| Story | `userstories_userstory` | `userstories_userstory_assigned_users` when an assignee is set; `epics_relateduserstory` when linked to an epic |
| Issue | `issues_issue` | — |
| Task | `tasks_task` | FK to the parent story when `parent:` is set |
| Epic | `epics_epic` | — (colour is randomly generated) |
| Milestone | `milestones_milestone` | — (no ref; milestones sit outside the ref sequence) |

Every insert sets `created_date` and `modified_date` (UTC now), `version = 1`
(Django's optimistic-concurrency field), and the schema's NOT NULL housekeeping
columns that Django would normally default.

## Updates

An update rewrites the row's content fields and refreshes `modified_date`.
Before writing, taigun compares the row's current `modified_date` against the
sidecar's `last_pushed_at` — a Taiga-side edit since the last push is a conflict
and prompts before overwriting.

## What is never written

Because Django signals do not fire on direct writes, taigun produces:

- No history entries (`history_historyentry`)
- No timeline entries (`timeline_timeline`)
- No notifications (email or in-app)
- No websocket events — open Taiga boards will not live-update

Tickets appear in the UI on next page load, with no audit trail of their
creation. If any of the above matter for your use, the official Taiga REST API is
the right tool instead.
