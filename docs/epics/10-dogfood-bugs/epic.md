---
type: epic
project: taigun
---

## E10 — Bugs surfaced by dog-food coverage pass

### Context

E8 025 kicked off the full dog-food coverage pass — push each ticket type to a
fresh Taiga project on the lab, verify each renders. Because taigun's code up
to this point has only been exercised against `test-db` (no API) and one
sub-tree of push targets at a time, the wider dog-food surface is turning up
bugs the unit tests can't see.

This epic collects each of those bugs as its own ticket so they can be
triaged, fixed, and regressed against, rather than lumped into 025 itself.

### In scope

- Any bug found while running the 025 dog-food pass
- Each ticket carries its reproducer and a proposed fix (per B: "not insane")

### Out of scope

- New taigun features. Bugs only.
- Cleanup of pre-existing tech debt unrelated to the dog-food findings

### Dependencies

- 025 (source of the bugs)
