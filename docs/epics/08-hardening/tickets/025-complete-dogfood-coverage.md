---
type: story
project: taigun
assignee: bmcivor
---

## 25. Complete dog-food coverage for tasks, issues, and linkages

**As a** taigun developer
**I want** every supported ticket type and link relationship pushed to a real Taiga at least once
**So that** v1.0 isn't trusting "it parses and resolves" as a proxy for "it works in the UI"

**Priority:** High

### Context

During v1.0 dog-fooding (taigun + vertex-play), only `story` and `epic` ticket types
were pushed. `task` and `issue` writers are unit-tested and dry-run-validated against
`test-db`, but neither has ever rendered in a real Taiga. The same goes for tag
propagation, parent-task → user-story linking, and story → epic linking.

Each of those code paths has the same risk profile as the bugs we found and fixed for
projects/stories: a NULL field the Taiga API serializer can't handle, a default
relation that's missing, or a join column we didn't populate. The way to find them is
to push one of each, into a real Taiga, and look at the UI.

### Acceptance criteria

- One task pushed to a fresh real-Taiga project — visible in the UI under its parent
  user story
- One issue pushed — visible in the Issues tab, with priority/severity/type populated
- One story with `tags: foo, bar` in frontmatter — UI shows both tags on the story
  detail page
- One task with `parent: <story-ref>` — UI shows the task linked to the parent story
- One story with `epic: <epic-ref>` — UI shows the story under the epic's "Related
  user stories"
- Any bugs surfaced by the above are fixed (same pattern as the v1.0 fixes:
  populate missing fields in the writer, patch the lab data if needed, update tests)
- Outcome documented — either "all green" or "fixed N bugs, listed here"
- **API-render check per pushed item**: after each push, hit the Taiga API for
  the created resource (project, story, task, issue, epic) and confirm 200 OK
  — this is the coverage that 029 was going to buy with a full back container.
  Postponing 029 in favour of doing this here means the dog-food pass is the
  only line of defence against NULL-field serializer crashes, so don't skip it

### Dependencies

- v1.0 released
