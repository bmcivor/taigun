# Ticket format

taigun parses markdown files with a YAML frontmatter block followed by a structured
markdown body. The format is derived from the vertex-play ticket convention with the
addition of a frontmatter block for machine-readable metadata.

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
| `type` | Yes | all | `story`, `issue`, `task`, `epic` |
| `project` | Yes | all | Project slug (see `taigun projects list`) |
| `epic` | No | story, task | Epic ref number to link to |
| `assignee` | No | all | Taiga username |
| `milestone` | No | story, issue, task | Sprint/milestone name |
| `tags` | No | all | Comma-separated list |
| `status` | No | all | Status name — defaults to first status for the project |
| `parent` | No | task | Parent user story ref number |

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
| `### Priority` | `priority` FK |

### Issue

Same as user story body, with two additional frontmatter fields:

| Frontmatter field | Maps to | Values |
|---|---|---|
| `issue_type` | `type` FK | `Bug`, `Question`, `Enhancement` |
| `severity` | `severity` FK | `Critical`, `High`, `Normal`, `Low`, `Wishlist` |

### Task

Same as user story body. `parent` frontmatter field links to a user story by ref number.

### Epic

Same as user story body, minus the As a / I want / So that block.

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
