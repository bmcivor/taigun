# Milestones (sprints)

Milestones — Taiga's word for sprints — are created the same way as tickets: a
markdown file with `type: milestone`, pushed with `taigun push`.

## The file

```markdown
---
type: milestone
project: my-project
estimated_start: 2026-08-01
estimated_finish: 2026-08-14
---

## Sprint 3
```

`estimated_start` and `estimated_finish` (`YYYY-MM-DD`) are required. Two optional
fields: `closed: true` marks the sprint as closed, and `assignee: <username>` sets
the milestone owner (defaults to the acting user).

!!! warning "Title only — no body"
    Taiga's `milestones_milestone` table has no description column, so a milestone
    file's body must contain only the `## Title` heading. Anything after the title
    is a `ParseError`.

## Pushing

```
$ taigun push ~/Tickets/my-project/sprint-3.md
✓ milestone: "Sprint 3"
```

Milestones have no ref number in Taiga, so the output carries no `#N` — but the
sidecar still tracks the file, and re-pushing an edited milestone updates the same
sprint. Conflict detection works as for tickets; the explicit `field: null`
clearing rule does not apply to milestones.

## Putting tickets in a sprint

Stories, issues, and tasks join a sprint via the `milestone:` frontmatter field,
matching the milestone's name:

```yaml
---
type: story
project: my-project
milestone: Sprint 3
---
```

## Closing a sprint

Set `closed: true` in the milestone file and re-push:

```
$ taigun push ~/Tickets/my-project/sprint-3.md
↺ milestone: "Sprint 3" (updated)
```
