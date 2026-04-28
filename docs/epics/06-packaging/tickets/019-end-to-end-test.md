## 19. End-to-end test against vertex-studio Taiga

**Epic:** E6 — Packaging & release

**As a** developer
**I want** to push one of each ticket type to the vertex-studio Taiga instance
**So that** the full flow is verified against a real database before release

### Acceptance criteria

- One story, one issue, one task, and one epic pushed successfully
- All four appear in the Taiga UI on the correct project board
- Ref numbers are correct and sequential (no gaps, no duplicates)
- All fields set in the test tickets display correctly in the UI
- Task with a parent story shows the parent link in the UI
- Story linked to an epic shows the epic in the UI
- No DB errors or constraint violations during the push
- `taigun push --dry-run` on the same files completes without error

### Dependencies

- 016, 018
- 001 (Postgres accessible over Tailscale)

### Blocks

- None

### Priority

- High
