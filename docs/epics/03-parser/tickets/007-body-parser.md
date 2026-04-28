## 7. Body section parser

**Epic:** E3 — Markdown parser

**As a** developer
**I want** the markdown body parsed into subject and description fields
**So that** the full ticket model is populated and ready for the DB writer

### Acceptance criteria

- `## Title` → `subject` (text only, no `##`)
- `### Priority` section value → `priority` field on the model; section is not included
  in the assembled description
- All other `###` sections assembled into `description` in order, headings preserved
- As a / I want / So that block preserved verbatim in description
- Body with no `## Title` → raises `ParseError`
- `parse_file(path)` is the public entry point — reads file, runs frontmatter + body
  parsing, returns a fully populated dataclass
- Epic ticket type: no user story block expected or required

### Dependencies

- 006

### Blocks

- 016

### Priority

- High
