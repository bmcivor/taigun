# Dog-food audit (ticket 030)

Audit of what fields/sections actually land in Taiga on push, vs what was in the source markdown. Diagnostic only — fixes go to ticket 031.

## Method

- **Sample 1** — fresh synthetic story pushed to a clean local `test-db` project (`audit-test`, story ref #1). Designed to populate every supported frontmatter field and body section. Untouched by UI fiddling, so the DB row reflects push-time state exactly.
- **Sample 2** — vertex-play epic ref #1 on the lab (`E1 — Lab integration and Jenkins onboarding`). Pushed earlier this session, hasn't been edited.
- **Not used as authoritative** — vertex-play story ref #9 on the lab. Its row has been touched externally since push (status changed to Done, assigned_to_id set without M2M backing) so its current state can't be cleanly attributed to push-time behaviour.

## Findings

### Bugs (push-time, reproducible)

1. **`**As a** / **I want** / **So that` block dropped from description.**
   - Root cause: `taigun/parsers/body.py:41` — `re.split(r"^### ", body, flags=re.MULTILINE)[1:]` discards everything before the first `### ` heading, including the user-story preamble between `## Title` and the first `###` section.
   - Severity: high. Affects every story/task/issue/epic ticket with a user-story block.
   - Reproduced: synthetic story (sample 1) source has the block; DB description starts directly at `### Context`. Block is gone.

2. **Blank line between `### Heading` and content stripped.**
   - Root cause: `taigun/parsers/body.py:44` — `content = content.strip()`.
   - Severity: low (markdown still renders; just style drift). Source has `### Context\n\nText`, DB has `### Context\nText`.
   - Reproduced: both samples.

3. **`### Priority` on stories has nowhere to go.**
   - Root cause: Taiga's `userstories_userstory` table has no `priority_id` column. Only `issues_issue` does. The parser extracts the priority value, the resolver resolves it against `projects_priority`, then the writer has nowhere to store it. Silently dropped.
   - Severity: medium. Same likely applies to `task` and `epic` (not yet confirmed against schema in this audit — should be confirmed in 031).
   - Per-product decision (B confirmed): fix in 031 by erroring on `### Priority` for non-issue ticket types. Force user to remove the section.
   - Reproduced: sample 1 has `### Priority: High`, push succeeded with no error, no priority data anywhere in DB.

### Confirmed OK

- `subject` — landed correctly (sample 1: "99. Audit synthetic story..."; sample 2: "E1 — Lab integration and Jenkins onboarding"). Title number kept as-is in subject; that's per current spec.
- `tags` — frontmatter `tags: foo, bar, baz` → `tags={foo,bar,baz}` text array. Round-trips correctly.
- `status` — frontmatter `status: Ready` → `status_id=2` (the "Ready" status on the audit-test project). Resolved correctly.
- `assignee` — frontmatter `assignee: admin` → `assigned_to_id=5` AND `userstories_userstory_assigned_users` M2M populated with user 5. Both the column and the M2M get set.
- All `###` sections other than Priority — `### Context`, `### Acceptance criteria`, `### Scope boundary`, `### Dependencies`, `### Blocks` — heading and content land in description. Content drifts only by the blank-line bug above.
- Frontmatter `type` and `project` — used to route to the right writer / project_id. Working.
- Static-default columns (`is_blocked=false`, `blocked_note=''`, `is_closed=false`, `client_requirement=false`, `team_requirement=false`, `due_date_reason=''`) — set to safe defaults by the writer.

### Not audited (no source field exercises this code path)

- `epic` (story → epic link by ref). Source synthetic ticket didn't set this. Covered by 025.
- `parent` (task → user story link by ref). Tasks not exercised at all. Covered by 025.
- `milestone`. Would have required pre-creating a milestone on the audit project (no MilestoneWriter — see 028). Skipped.
- `issue_type` / `severity`. Issues not exercised at all. Covered by 025.

## Bugs checklist for 031

- [ ] Fix `BodyParser` to include the pre-first-`###` content (the As a/I want/So that block) at the start of `description`.
- [ ] Fix `BodyParser` content `.strip()` so blank lines between heading and content are preserved.
- [ ] Verify `tasks_task` and `epics_epic` schema for priority column (likely also missing) → error on `### Priority` for `story`, `task`, `epic` types. Only `issue` should accept it.
- [ ] Add parser tests covering: As a/I want/So that block preserved, blank lines preserved between heading and content, error raised on `### Priority` for non-issue types.
