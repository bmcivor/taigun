## 6. Frontmatter parser

**Epic:** E3 — Markdown parser

**As a** developer
**I want** the YAML frontmatter block parsed into a partial ticket model
**So that** machine-readable fields are extracted before body parsing begins

### Acceptance criteria

- `parser.py` uses `python-frontmatter` to split frontmatter from body
- All frontmatter fields parsed: `type`, `project`, `epic`, `assignee`, `milestone`,
  `tags`, `status`, `parent`, `issue_type`, `severity`
- `type` and `project` missing → raises `ParseError` with the field name
- Unknown frontmatter keys → raises `ParseError` naming the unexpected key
- `tags` accepts both a comma-separated string and a YAML list
- Returns a partial dataclass instance (body fields left empty at this stage)

### Dependencies

- 005

### Blocks

- 007

### Priority

- High
