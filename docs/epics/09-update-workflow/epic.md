---
type: epic
project: taigun
assignee: bmcivor
---

## E9 — Update workflow

### Context

taigun is currently push-only — there is no way to update a ticket after the first push. Edits to the markdown source don't propagate to Taiga; the only path to changing a ticket is the Taiga UI, after which the markdown is silently out of date.

This was a design omission, not an intentional constraint. For any workflow where documentation is meant to stay in sync with Taiga tickets (or vice versa), it's a hole. This epic closes it.

### Surface area

Three pieces:

1. **Decide how to identify a ticket on second push** — Taiga ref written back to frontmatter, content hash, slug uniqueness, something else. Documented as an ADR.
2. **Round-trip refs** — push writes the assigned ref back to the source file so subsequent invocations can use it.
3. **Implement update / upsert** — read the ref, look up the existing ticket, compute what changed, apply the changes via UPDATE SQL.

### In scope

- ADR documenting the identification + update semantics
- Frontmatter changes (add `taigun_ref`) and push writing it back
- New CLI command (`taigun update` or upsert behaviour on `push`)
- Field-level decisions: which fields are mutable, what happens to fields that disappear from frontmatter, error semantics for immutable fields

### Out of scope

- Sync direction the other way (Taiga → markdown). One-way for now.
- Deletes. Delete-via-markdown-removal is gnarly and not needed yet.

### Dependencies

- E8 031 (push must be lossless before update can be meaningfully tested)
