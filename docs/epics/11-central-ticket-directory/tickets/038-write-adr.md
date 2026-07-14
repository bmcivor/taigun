---
type: story
project: taigun
assignee: bmcivor
status: Done
---

## 38. Write ADR-005 for the central ticket directory

**As a** taigun contributor considering the "where do ticket files live" question
**I want** a written decision on the destination, the reasoning, and the migration approach
**So that** the move isn't undone later by someone who wasn't in the room for the discussion, and every downstream migration (vertex-play, vertex-block, vertex-studio) can reference a single source of truth

### Context

The current taigun workflow puts `docs/epics/` in each product source repo. Two problems: product-repo history is polluted with ticket-tracking commits, and the sidecar (per-user state) sits in a shared repo where it produces meaningless merge conflicts.

The decision to move to a central `~/Tickets/` directory needs an ADR so:

- The reasoning is captured and reviewable (not just verbal).
- The destination layout is fixed enough that future migrations don't drift.
- The scope of what the ADR does and does not enforce is explicit (e.g. taigun does not pin `~/Tickets/` as a path — it locates itself via `.git/` walk-up).

### Acceptance criteria

- ADR-005 exists at `docs/decisions/ADR-005-central-ticket-directory.md`.
- Status is `Accepted` once merged.
- Covers: layout (repo root, per-project sub-directory, preserved ticket tree, sidecar location), frontmatter contract (`project:` remains the authoritative dispatch key), migration approach (per-repo `git mv`, delete + re-push on the lab, sidecar not migrated in-place), and out-of-scope items (path is not enforced, vertex-* migrations owned by their own repos, no taigun code change, no update to ADR-004).
- Cross-referenced by the E11 epic and by 039 / 040.

### Dependencies

- 036 (the walk-up-to-`.git/` fix is a prerequisite for the ADR's claim that `~/Tickets/` "just works")
