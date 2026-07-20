# ADR-002 — Markdown ticket format

## Status

Accepted

## Decision

taigun uses a markdown format with YAML frontmatter for machine-readable fields,
derived from the vertex-play ticket convention.

## Reasoning

The vertex-play project already uses a structured markdown ticket format. taigun
extends it minimally — the only addition is a YAML frontmatter block for fields
that need to be machine-readable (type, project slug, assignee, etc.).

The body format (user story block, acceptance criteria, context, dependencies,
blocks, priority) is preserved unchanged. Existing vertex-play tickets require
only a frontmatter block added to be pushable with taigun.

## Format summary

```
---
type: story | issue | task | epic
project: <slug>
[optional fields: epic, assignee, milestone, tags, status, parent, issue_type, severity]
---

## Title

[user story block — stories/issues/tasks]

### Acceptance criteria
### Context (optional)
### Scope boundary (optional)
### Dependencies
### Blocks
### Priority
```

See `docs/ticket-format.md` for the full specification.

## Alternatives considered

**Pure frontmatter** — put all fields in YAML, use description as a freeform body.
Rejected: loses the structured, human-readable format that makes tickets useful as
standalone documents.

**Different file format (TOML, JSON)** — rejected: markdown is already the convention
in the projects taigun is designed to serve.
