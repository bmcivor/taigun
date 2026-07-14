---
type: story
project: taigun
assignee: bmcivor
---

## 39. Migrate taigun's own tickets out of the source repo

**As a** taigun contributor
**I want** taigun's own `docs/epics/` tree moved into `~/Tickets/taigun/docs/epics/` and pushed from there
**So that** taigun eats its own dogfood on the very design ADR-005 prescribes, and the pattern is proven end-to-end before we replicate it in other repos

### Context

ADR-005 sets the destination. This ticket does the actual move for the taigun repo and verifies the whole cycle works: git move → sidecar path-rewrite → push is a no-op against the lab (content-hashes unchanged, refs preserved).

The Taiga project on the lab is **not** deleted. Because `git mv` doesn't change file bytes, the sidecar's `content_hash` values still match, and rewriting only the `file_path` fields (from `docs/epics/…` to `taigun/docs/epics/…`) is enough to keep every entry pointing at the correct existing ref. Push then reports `(unchanged) #N …` for all 51 entries and writes nothing to Taiga.

### Acceptance criteria

- `~/Tickets/` exists as a git repo (`git init` if not already).
- The taigun source repo's entire `docs/epics/` tree is `git mv`'d to `~/Tickets/taigun/docs/epics/`, preserving epic/tickets structure. The source-repo commit removes `docs/epics/` and only `docs/epics/` (README, ADRs, ticket-format.md, planning-status.md, decisions/, dog-food-audit.md all stay in the source repo).
- The sidecar is moved to `~/Tickets/.taigun/state.yaml` with `file_path` values rewritten to be relative to the new repo root (`taigun/docs/epics/…`). `content_hash`, `ref`, `project`, `ticket_type`, and `last_pushed_at` stay untouched.
- A push from `~/Tickets/` against the same lab project reports `(unchanged) #N …` for every entry and makes no Taiga writes.
- No taigun code change is made under this ticket — the migration succeeds using the CLI as it stands after 036.
- The E11 epic dir moves with the rest (so the ticket that describes moving itself ends up correctly under `~/Tickets/taigun/docs/epics/11-...`).

### Dependencies

- 038 (ADR must be accepted before the move)
- 036 (sidecar location fix; without it, the multi-project batch push from `~/Tickets/` would fail on the first cross-directory file)
