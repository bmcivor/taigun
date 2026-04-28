## 16. push command

**Epic:** E5 — CLI

**As a** user
**I want** `taigun push` to parse and insert one or more ticket files
**So that** I can push tickets to Taiga from the command line in a single step

### Acceptance criteria

- `taigun push <file>` pushes a single ticket
- `taigun push <glob>` (e.g. `taigun push tickets/*.md`) pushes all matched files
- Per-file output: `✓ #42 story: "Title of the ticket"` on success, error message on failure
- `--dry-run` flag: parses and resolves all FKs but does not insert — prints what
  would be pushed
- `--profile <name>` flag: use a named config profile (default: `default`)
- Failures on individual files do not abort remaining files — all are attempted
- Exit code 0 if all succeeded, 1 if any failed

### Dependencies

- 007, 011, 012, 013, 014, 015

### Blocks

- 019

### Priority

- High
