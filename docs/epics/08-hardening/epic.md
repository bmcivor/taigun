---
type: epic
project: taigun
assignee: bmcivor
---

## E8 — v1.0 hardening

### Context

Post-1.0 cleanup epic. Covers the gaps surfaced during dog-fooding taigun + vertex-play
against the lab Taiga, and the test/CI scaffolding that's currently held together with
acknowledged shortcuts.

None of these block v1.0 — but each is a known issue that should be cleaned up via
patch releases before the next major.

### Surface area

1. **Real-Taiga dog-food gaps.** Only story and epic ticket types have been pushed to
   a running Taiga. Task, Issue, tag propagation, parent-task linking, and epic-link
   resolution are unit-tested + dry-run-validated only.
2. **Test scaffolding hacks.** `cli_conn` fixture uses `monkeypatch.setattr` on
   `psycopg2.connect`; `docs/` is baked into the test image as a temporary
   workaround.
3. **Missing primitive.** `MilestoneWriter` does not exist, forcing raw SQL in
   `tests/factories.py::make_milestone` as a stop-gap.
4. **CI gap.** Integration tests run against `test-db` only — the actual Taiga API
   server is never exercised in CI, so the class of NULL-field bug we hit twice
   during dog-fooding can recur and won't be caught until lab dog-food.

### In scope

- Dog-food the remaining ticket types and link relationships against a real Taiga
- Replace test-only hacks with proper test seams in production code
- Add MilestoneWriter
- Add CI stage that runs taigun against a real Taiga back container

### Out of scope

- New ticket types (we only support the four Taiga has)
- Update/delete operations on existing tickets (taigun is push-only by design)
- Taiga version bump (would be its own work — current target is 6.9.0)

### Dependencies

- v1.0 released (sets the baseline these patches will land on top of)
