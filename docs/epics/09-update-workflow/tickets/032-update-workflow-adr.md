---
type: story
project: taigun
---

## 32. Design update workflow (ADR)

**As a** taigun developer
**I want** the update-workflow design committed as an ADR before any code is written
**So that** the semantics around ticket identification, mutability, and error handling are decided once and visible, not invented per-PR

### Context

The interesting decisions are not the SQL — they're the workflow shape. Things to resolve in this ticket, not in implementation:

- **Identification: use a sidecar file.** `.taigun-state.json` (or similar) at repo root maps source file path → Taiga ref. Push reads it to decide insert vs update; writes it after successful insert. Source files never get touched by taigun, no YAML round-tripping problem, the mapping is explicit and committable. Rejected alternatives:
  - `taigun_ref` written back into frontmatter — YAML libraries mangle key order / strip comments / change quoting, hostile to git diffs
  - Query Taiga first by subject or content — no naturally stable key in Taiga's schema (subjects are mutable, hashes change with every edit), would require adding a marker field anyway, which is just a sidecar in a worse place
- **Sidecar shape**: file format (TOML / JSON / YAML), location (repo root vs `.taigun/`), what's stored beyond the ref (project, push timestamp, content hash for change detection?), whether one sidecar per repo or per project
- **Mutability**: which fields can change? Title and description obviously. Status? Priority? Milestone? Type? Project itself?
- **Removal semantics**: if a frontmatter field is present on push 1 but absent on push 2, do we (a) clear that field, (b) leave it as-is, (c) error?
- **Conflict semantics**: if Taiga has been edited in the UI since the last push, do we (a) overwrite blindly, (b) detect via `modified_date` and refuse, (c) detect and prompt?
- **Missing-ticket semantics**: if the sidecar points at a ref that no longer exists in Taiga (deleted via UI), do we (a) error, (b) re-insert and update the sidecar, (c) prompt?
- **Idempotency**: re-pushing an unchanged file should be a no-op, not a 200-row update
- **Audit trail**: when an update lands, what value goes in Taiga's "modified by" column (whatever Taiga has) — `acting_user` from config seems right but confirm

### Acceptance criteria

- ADR file at `docs/decisions/ADR-NNN-update-workflow.md`
- Covers each decision above with: chosen option, rejected options, rationale
- References the existing ADRs for taigun's design philosophy (direct DB writes, etc.) where relevant
- Reviewed by B before any of 033/034 starts

### Dependencies

- E8 031 (push needs to be lossless first, or the ADR's idempotency claims are nonsense)

### Blocks

- 033, 034

### Priority

- High (gates all the update code)
