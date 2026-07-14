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

ADR-005 sets the destination. This ticket does the actual move for the taigun repo and verifies the whole cycle works: git move → re-push → sidecar populates correctly → tickets render in Taiga as they did before, except now the sidecar sits at `~/Tickets/.taigun/state.yaml` and product-repo history is done taking ticket-tracking commits.

### Acceptance criteria

- `~/Tickets/` exists as a git repo (`git init` if not already).
- The taigun source repo's entire `docs/epics/` tree is `git mv`'d to `~/Tickets/taigun/docs/epics/`, preserving epic/tickets structure. The source-repo commit removes `docs/epics/` and only `docs/epics/` (README, ADRs, ticket-format.md, planning-status.md, decisions/, dog-food-audit.md all stay in the source repo).
- Taiga project `taigun` on the lab is deleted before the re-push (per the pattern established in the earlier dogfood pass — sidecar and Taiga state need to line up from empty).
- Re-push runs from `~/Tickets/` and pushes every taigun epic + ticket to Taiga successfully. Sidecar entries carry paths relative to the `~/Tickets/` root (e.g. `taigun/docs/epics/01-infrastructure/epic.md`), not relative to the old source-repo root.
- No taigun code change is made under this ticket — the migration succeeds using the CLI as it stands after 036.
- The E11 epic dir moves with the rest (so the ticket that describes moving itself ends up correctly under `~/Tickets/taigun/docs/epics/11-...`).

### Dependencies

- 038 (ADR must be accepted before the move)
- 036 (sidecar location fix; without it, the multi-project batch push from `~/Tickets/` would fail on the first cross-directory file)
