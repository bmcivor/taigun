---
type: story
project: taigun
---

## 33. Round-trip taigun_ref in frontmatter

**As a** taigun user
**I want** push to write the assigned Taiga ref back into my source markdown
**So that** my markdown becomes the link between source and Taiga ticket, with no manual bookkeeping

### Context

Assumes the ADR (032) lands on `taigun_ref` as the identification mechanism. After push:

```yaml
---
type: story
project: vertex-play
taigun_ref: 42        # written back by push
---
```

The frontmatter parser already understands unknown fields can be loaded into the model. This ticket extends it so the field is also writable back to the file after a successful push.

Open question for the ADR: write back always, or behind a flag (`--write-refs`). Behind a flag is safer (push stays read-only by default) but pushes the user to remember to use it. Always-on is more useful but mutates the user's file as a side effect of `push`. Decide in 032.

### Acceptance criteria

- Frontmatter parser reads `taigun_ref` from input files (already loads unknown fields — verify)
- Push, on success, writes the new ref back to the source file's frontmatter — exact mechanism per 032
- The rewrite preserves the rest of the file byte-for-byte (no reordering, no quote-style changes, no whitespace shuffling) — frontmatter libraries often round-trip poorly, may need custom write
- Unit tests covering: write into a file with no existing `taigun_ref`, overwrite an existing one, leave other frontmatter fields untouched
- All existing tests still pass

### Dependencies

- 032

### Blocks

- 034

### Priority

- Medium
