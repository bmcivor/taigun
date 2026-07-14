---
type: story
project: taigun
assignee: bmcivor
---

## 40. Update taigun docs and the taigun-tickets skill for the central-directory workflow

**As a** taigun user reading the README (or Claude reading the skill)
**I want** the current documented workflow to match the ADR-005 reality
**So that** the first thing anyone tries is not "add `docs/epics/` back into my product repo" because that's what the docs still tell them to do

### Context

The taigun README, `docs/ticket-format.md`, and the `taigun-tickets` skill (`~/.claude/skills/taigun-tickets/SKILL.md`) all currently describe running taigun from within a product source repo. After 039 lands, that instruction is out of date and actively misleading — anyone following the README will put tickets back in the wrong place.

The changes are text-only, no code, no test. Scope is: describe the central `~/Tickets/` layout, describe how to point taigun at it, describe where the sidecar ends up, remove any instruction that assumes `docs/epics/` is in-repo.

### Acceptance criteria

- `README.md`: workflow section describes running taigun from a `~/Tickets/`-style central directory, with per-project sub-directories.
- `docs/ticket-format.md`: no change to the format itself — but the "where do these files live" preamble points at the central directory, not the source repo.
- `~/.claude/skills/taigun-tickets/SKILL.md`: same update; any example paths use `~/Tickets/<project>/docs/epics/...` shape.
- No taigun code touched; no tests touched.
- Nothing added that contradicts ADR-005 (path enforcement, migration helper CLI, etc. all stay out).

### Dependencies

- 038 (ADR-005 must be accepted so the docs describe an accepted decision, not a proposal)
- 039 (the migration must have actually happened before the docs describe it as the current workflow)
