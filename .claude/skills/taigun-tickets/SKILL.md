---
name: taigun-tickets
description: Write tickets in the taigun markdown format and push them to a Taiga instance via the taigun CLI. Use this skill whenever the user wants to write project tickets (stories, epics, tasks, issues, milestones), convert existing tickets to taigun format, push tickets to Taiga, or update already-pushed tickets. Triggers on phrases like "write tickets", "write tickets for X", "fire them off to Taiga", "push these to Taiga", "add this to Taiga", "convert these to taigun format", "mark ticket done", "update the ticket status", "dog-food tickets". Covers the YAML frontmatter spec, body structure, where files live (per-user central directory, not per-repo), how to invoke the CLI, and known pitfalls (epic-ref two-pass, project must exist, priority being issue-only, sidecar-anchor requirement).
---

# Taigun ticket workflow

## What it is

`taigun` is a Python CLI that writes Taiga tickets directly to Taiga's PostgreSQL database, bypassing the Taiga API. Tickets are markdown files with YAML frontmatter; `taigun push` parses them, resolves FK references against the live DB, and inserts or updates.

Format spec is the source of truth: `~/Development/Lab/taigun/docs/ticket-format.md`. Read it when in doubt — anything below is a working summary.

## Ticket format

Frontmatter is YAML. `type` and `project` are required. `status` is optional (defaults to the project's default status for that type).

| Field | Required | Applies to | Notes |
|---|---|---|---|
| `type` | Yes | all | `story`, `issue`, `task`, `epic`, `milestone` |
| `project` | Yes | all | Project slug, must exist before push |
| `status` | No | all | Status name; use `Done` for completed work. Unknown names warn and fall back to the project default (037) |
| `epic` | No | story, task | Epic **ref** number (not slug) — see two-pass note below |
| `parent` | No | task | Parent user-story ref number |
| `assignee` | No | all | Taiga username |
| `milestone` | No | story, issue, task | Sprint/milestone name; must exist |
| `tags` | No | all | Comma-separated string or YAML list |
| `issue_type` | No | issue | `Bug`, `Question`, `Enhancement` |
| `severity` | No | issue | `Critical`, `High`, `Normal`, `Low`, `Wishlist` |
| `priority` | No | **issue only** | see note below |
| `estimated_start` | Yes | milestone | Sprint start date (`YYYY-MM-DD`) |
| `estimated_finish` | Yes | milestone | Sprint end date (`YYYY-MM-DD`) |
| `closed` | No | milestone | Bool — sprint closed. Default false |

Body structure (stories/tasks):

```markdown
## NN. Title

**As a** [role]
**I want** [goal]
**So that** [reason]

### Acceptance criteria

- ...

### Context
(optional, free text)

### Scope boundary
(optional)

### Dependencies
- 002, 003

### Blocks
- 005
```

Epics use the same structure minus the As a / I want / So that block, with `## EN — Title`. All `###` sections are concatenated into the ticket's description verbatim.

Milestones are minimal — frontmatter plus `## Title` and nothing else. Taiga's `milestones_milestone` table has no description column, so any content after the title raises `ParseError`.

**Priority is issue-only.** Taiga's schema has no priority column for stories, tasks, or epics. Adding a `### Priority` section or `priority:` frontmatter field to any of those types raises `ParseError`. Issues can use either or both. For stories/tasks/epics that _informally_ want to note importance, put `**Priority:** High` inline in the body — it lands in the description as plain text.

**Clearing a previously-set field.** Once a ticket has been pushed, dropping a frontmatter field on the next push errors (`FieldClearedError`). Clearing requires an explicit `field: null` so accidental deletions are loud.

## Where new tickets live

Per **ADR-005** (Accepted 2026-07-13): ticket source files live in a **per-user central directory**, not in the product source repos. The intended layout:

```
~/Tickets/                       <-- user-chosen root
├── .taigun/state.yaml           <-- one sidecar for every project
├── taigun/
│   └── docs/epics/NN-<slug>/{epic.md, tickets/NNN-<slug>.md}
├── vertex-play/
│   └── docs/epics/...
└── vertex-block/
    └── docs/epics/...
```

Rules:

- One sub-directory per Taiga project, named after the project slug.
- Inside each sub-directory, the existing `docs/epics/<NN>-<kebab-name>/{epic.md, tickets/}` structure is preserved.
- Ticket numbers are project-wide and monotonically increasing across all its epics.
- `.taigun/state.yaml` sits at `~/Tickets/.taigun/state.yaml`. It tracks the file → Taiga ref mapping, content hashes for idempotency, and last-pushed timestamps for conflict detection.

`project:` in the ticket's frontmatter remains the authoritative dispatch key. Directory location is a filesystem convention for humans to navigate; taigun does not enforce or infer the project from the path.

**Do not add `docs/epics/` back into a product source repo.** Every taigun-managed edit becomes a commit — that's what moved out of source repos in the first place.

## Push workflow

taigun runs **natively via `uv run`**. No docker for the CLI itself.

### 1. One-time setup

Config lives at `~/.config/taigun/config.toml`:

```toml
[default]
host = "shadowlands.tail252efc.ts.net"
port = 5432
database = "taiga"
username = "taiga"
password = "changeme"          # tracked in vertex-studio/roles/taiga/templates/env.j2
acting_user = "bmcivor"
```

Or run `uv run taigun configure` inside `~/Development/Lab/taigun` for the interactive setup.

If `~/Tickets/` doesn't have a sidecar yet, seed it before the first push (else `locate_sidecar` errors out):

```bash
mkdir -p ~/Tickets/.taigun && touch ~/Tickets/.taigun/state.yaml
```

### 2. Make sure the project exists on the Taiga side

```bash
uv run --project ~/Development/Lab/taigun taigun projects list
uv run --project ~/Development/Lab/taigun taigun projects create "Display Name" project-slug
```

Project creation materialises statuses, priorities, severities, issue types, points, and roles from the default template. This must run before any `push`.

### 3. Push the tickets

From `~/Tickets/` (or anywhere — paths can be relative or absolute):

```bash
cd ~/Tickets
uv run --project ~/Development/Lab/taigun taigun push <project>/docs/epics/*/epic.md
uv run --project ~/Development/Lab/taigun taigun push <project>/docs/epics/*/tickets/*.md
```

Push epics first so their refs exist when stories link to them.

Per-file output:

- `✓ #42 story: "Title"` — inserted, new ticket
- `(unchanged) #42 story: "Title"` — sidecar hash matches, no-op
- `↺ #42 story: "Title" (updated)` — content changed, updated in Taiga
- `↷ #42 story: skipped (Taiga was edited)` — conflict; someone edited via UI. Re-run with `--force` to overwrite.

### 4. Dry-run first (recommended for anything non-trivial)

```bash
uv run --project ~/Development/Lab/taigun taigun push --dry-run <project>/docs/epics/*/*.md
```

`~ story: "…"` means "would push in a real run". Catches parse errors and missing FKs before hitting the real Taiga.

## Update workflow

Edit the source file → re-run `taigun push` on it. taigun looks up the file in the sidecar, dispatches to update instead of insert, and:

- Reports `(unchanged) #N …` if content hash matches — no-op.
- Reports `↺ #N … (updated)` if content changed — updates the Taiga row.
- Prompts if Taiga's `modified_date` is newer than `last_pushed_at` (someone edited via UI). `--force` skips the prompt and overwrites.
- Prompts if the file's sidecar entry points at a ref that no longer exists on Taiga (someone deleted it). `--force` re-inserts.

Immutable identity: `project` and `type` in the frontmatter cannot change on re-push — that errors as `IdentityChangeError` (it's a different ticket, not an edit).

## Pitfalls

**Story → epic linking needs two passes.** The `epic:` frontmatter field is the epic's Taiga ref number, assigned at push time. So: push epics first, note the refs from the output (e.g. `✓ #3 epic: "..."`), then add `epic: 3` to the relevant story frontmatter and push the stories.

**Project must be created before push.** If a project slug doesn't exist, `taigun push` fails on resolve. Run `taigun projects create` first.

**Sidecar location.** `locate_sidecar` walks up looking for an existing `.taigun/state.yaml`, then for `.git/` as a fallback anchor. If neither is found on the walk-up, it raises `StateError` — never silently places the sidecar at the first source file's parent. Fix by `mkdir ~/Tickets/.taigun && touch ~/Tickets/.taigun/state.yaml` at your intended root.

**Do not commit `~/Tickets/.taigun/state.yaml` to a shared remote.** The sidecar is per-user tracking state; sharing it produces meaningless merge conflicts (see ADR-005 rationale).

**Watch for NULL-field bugs on new projects.** Historically (fixed in ProjectCreator as of v1.0): `projects_project.tags_colors`, `projects_project.tags`, `projects_project.default_points_id`, and the module activation flags were left NULL/false on `projects create`, which crashed the Taiga API serializer and made the project's UI tabs blank. If a freshly created project's UI is broken, check those columns and the taiga-back logs for `dict()` / `length` errors.

**Cross-repo edits need approval.** Per project rules, editing files in another repo (e.g. converting vertex-play tickets from taigun's repo) requires explicit confirmation from B and a fresh branch in the target repo first.

## Confirming what you wrote

Sanity-check via the Taiga UI (`http://shadowlands:9000`) or by querying the lab DB directly. From WSL with `psycopg2` available:

```bash
uv run --project ~/Development/Lab/taigun python -c "
import psycopg2
c = psycopg2.connect(host='shadowlands.tail252efc.ts.net', port=5432, dbname='taiga', user='taiga', password='changeme')
with c.cursor() as cur:
    cur.execute('SELECT ref, subject FROM userstories_userstory WHERE project_id = %s ORDER BY ref', (PROJECT_ID,))
    for row in cur.fetchall(): print(row)
"
```

Tables: `epics_epic`, `userstories_userstory`, `tasks_task`, `issues_issue`, `milestones_milestone`. Cross-type refs: `references_reference`.
