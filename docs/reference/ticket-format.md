# Ticket format

taigun parses markdown files with a YAML frontmatter block followed by a structured
markdown body. The format is derived from the vertex-play ticket convention with the
addition of a frontmatter block for machine-readable metadata.

For how to organise ticket files across multiple projects (recommended: a per-user
central directory outside your product source repos), see the "Where to put your
tickets" section in the [README](../../README.md).

## Structure

```markdown
---
type: story
project: my-project-slug
epic: 3
assignee: blake
milestone: Sprint 1
tags: backend, auth
---

## Title of the ticket

**As a** [role]
**I want** [goal]
**So that** [reason]

### Acceptance criteria

- criterion one
- criterion two

### Context

Optional. Background information relevant to the ticket.

### Scope boundary

Optional. Explicit statement of what is in and out of scope.

### Dependencies

- None

### Blocks

- None

### Priority

- High
```

## Frontmatter fields

| Field | Required | Applies to | Description |
|---|---|---|---|
| `type` | Yes | all | `story`, `issue`, `task`, `epic`, `milestone` |
| `project` | Yes | all | Project slug (see `taigun projects list`) |
| `epic` | No | story, task | Epic ref number to link to |
| `assignee` | No | all | Taiga username |
| `milestone` | No | story, issue, task | Sprint/milestone name |
| `tags` | No | all | Comma-separated list |
| `status` | No | all | Status name — defaults to first status for the project |
| `parent` | No | task | Parent user story ref number |
| `estimated_start` | Yes | milestone | Sprint start date (`YYYY-MM-DD`) |
| `estimated_finish` | Yes | milestone | Sprint end date (`YYYY-MM-DD`) |
| `closed` | No | milestone | Boolean — whether the sprint is closed. Defaults to `false` |

## Body fields by type

### User story

| Field | Maps to |
|---|---|
| `## Title` | `subject` |
| As a / I want / So that | Top of `description` |
| `### Acceptance criteria` | Appended to `description` |
| `### Context` | Appended to `description` |
| `### Scope boundary` | Appended to `description` |
| `### Dependencies` | Appended to `description` |
| `### Blocks` | Appended to `description` |

### Issue

Same as user story body, plus `### Priority` mapping to the `priority` FK, and two additional frontmatter fields:

| Frontmatter field | Maps to | Values |
|---|---|---|
| `issue_type` | `type` FK | `Bug`, `Question`, `Enhancement` |
| `severity` | `severity` FK | `Critical`, `High`, `Normal`, `Low`, `Wishlist` |

### Task

Same as user story body. `parent` frontmatter field links to a user story by ref number.

### Epic

Same as user story body, minus the As a / I want / So that block.

### Priority is issue-only

Taiga's schema has no priority column for stories, tasks, or epics — only issues.
taigun raises `ParseError` if a `### Priority` section or `priority:` frontmatter
field appears on any non-issue ticket. Remove the section from those files.

### Milestone

Milestones (Taiga's word for sprints) are created by taigun the same way as
tickets — as markdown files with `type: milestone` in the frontmatter.
Taiga's `milestones_milestone` table has no description column, so a milestone
file's body must contain only the `## Title` heading. Anything after the title
raises `ParseError`.

| Body field | Maps to |
|---|---|
| `## Title` | `name` (slug is derived from name) |

Example milestone file:

```markdown
---
type: milestone
project: my-project
estimated_start: 2026-08-01
estimated_finish: 2026-08-14
---

## Sprint 3
```

Optional `closed: true` marks the sprint as closed. Optional `assignee: <username>`
sets the milestone owner (defaults to the acting user).

## Description assembly

The `description` field in Taiga is assembled from the markdown body in section order,
preserving all headings and content. The As a / I want / So that block is written as-is.
Sections that are not recognised as structured fields (Context, Scope boundary, etc.)
are included verbatim.

## Priority mapping

| Markdown value | Taiga priority name (default) |
|---|---|
| `High` | `High` |
| `Medium` | `Normal` |
| `Low` | `Low` |

Taiga priority names are project-specific. taigun matches case-insensitively and falls
back to the project's default priority if no match is found.

## Example: issue file

```markdown
---
type: issue
project: vertex-play
issue_type: Bug
severity: High
assignee: blake
tags: pipeline, signing
---

## Signing step fails silently when keystore path is wrong

**As a** pipeline developer
**I want** the signing step to fail loudly when the keystore path is misconfigured
**So that** the error is caught at build time rather than producing an unsigned AAB

### Acceptance criteria

- Build fails with a clear error message if `KEYSTORE_PATH` does not exist
- Error includes the resolved path that was checked

### Priority

- High
```
