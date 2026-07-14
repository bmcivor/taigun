---
type: epic
project: taigun
assignee: bmcivor
---

## E11 — Central ticket directory

### Context

taigun-managed tickets currently live under `docs/epics/` inside each product's source repo (`Lab/taigun/`, `Lab/vertex-play/`, etc.). Every ticket edit — status flip, new ticket added, completion — becomes a commit in the product repo history alongside actual product code changes. The blame log gets noisy, PR reviewers cannot separate code changes from ticket paperwork, and the sidecar (which is per-user tracking state) sits in a shared repo where it produces meaningless merge conflicts.

This epic moves the taigun-managed ticket source files out of product repos and into a single per-user Tickets directory that is itself a git repo. The layout inside each project sub-directory is preserved: `docs/epics/<NN>-<name>/{epic.md, tickets/}` stays exactly as it is today. See ADR-005 for the full design argument.

### Surface area

Three pieces:

1. **Design lock-in (ADR-005)** — settle the layout, the migration approach, and what is and isn't a taigun contract before any files move.
2. **Reference migration (taigun's own tickets)** — do the mechanical `git mv` for taigun's `docs/epics/` tree; delete the Taiga project on the lab; re-push from the new location. Everything works or it doesn't; this is the smoke test for the pattern.
3. **Doc + skill update** — the taigun README, `docs/ticket-format.md`, and the `taigun-tickets` skill all currently describe "run taigun in your product source repo". Those instructions get updated to describe the central-directory workflow so future-me and any future contributor don't undo it.

### In scope

- ADR-005 written and accepted.
- taigun repo's `docs/epics/` tree `git mv`'d to `~/Tickets/taigun/docs/epics/` and removed from the source repo in a single commit.
- Taigun project on the lab deleted and re-pushed from the new location so the new sidecar is populated cleanly from empty.
- taigun repo docs (README, ticket-format) updated to describe the central-directory workflow.
- `~/.claude/skills/taigun-tickets/SKILL.md` updated to match.

### Out of scope

- Migrating tickets in vertex-play / vertex-block / vertex-studio. Each of those is a separate mechanical move owned by its own repo; ADR-005 sets the destination but this epic doesn't do those moves.
- Any change to the taigun CLI. Push and sidecar already handle multi-project trees per file's `project:` frontmatter — verified before opening this epic.
- Any change to ADR-004 or the update workflow. Sidecar semantics, mutability, conflict detection, and the identity triple all stand.
- A migration helper CLI. One-shot `git mv` per repo is cheaper than the tool.

### Dependencies

- 036 (sidecar location fix — `locate_sidecar` anchors `.taigun/` to the nearest `.git/` walk-up, which is what makes `~/Tickets/` work as the sidecar root)
