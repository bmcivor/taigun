---
type: story
project: taigun
---

## 33. Sidecar state file for source-to-ref mapping

**As a** taigun user
**I want** push to maintain a sidecar file that maps source markdown files to their Taiga refs
**So that** subsequent pushes can find existing tickets and update them, without taigun ever touching the source files

### Context

Assumes the ADR (032) lands on a sidecar file for identification. The sidecar lives in the repo (committed alongside the source) and contains the path → ref mapping that push uses to decide insert vs update.

Exact format / location / schema decided in 032. Likely shape:

```toml
# .taigun-state.toml at repo root
[[entries]]
file = "docs/epics/01/tickets/001.md"
project = "vertex-play"
ref = 9

[[entries]]
file = "docs/epics/01/tickets/002.md"
project = "vertex-play"
ref = 10
```

### Acceptance criteria

- New module (e.g. `taigun/state.py`) reads + writes the sidecar
- Push reads the sidecar on startup; for each source file in the push, looks up an existing entry
- After a successful insert, push writes a new entry to the sidecar
- Source markdown files are never written to by push
- Sidecar is robust to manual editing (e.g. user reorders or removes entries by hand — should not crash)
- Missing sidecar on first-ever push is fine (treated as empty)
- Unit tests covering: read missing file, read corrupted file, write new entry, write second entry without disturbing first
- All existing tests still pass

### Dependencies

- 032

### Blocks

- 034

### Priority

- Medium
