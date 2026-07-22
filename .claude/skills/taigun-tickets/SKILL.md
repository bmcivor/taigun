---
name: taigun-tickets
description: Write tickets in the taigun markdown format and push them to a Taiga instance via the taigun CLI. Use this skill whenever the user wants to write project tickets (stories, epics, tasks, issues, milestones), convert existing tickets to taigun format, push tickets to Taiga, or update already-pushed tickets. Triggers on phrases like "write tickets", "write tickets for X", "fire them off to Taiga", "push these to Taiga", "add this to Taiga", "convert these to taigun format", "mark ticket done", "update the ticket status", "dog-food tickets". Covers where ticket files live (per-user central directory, not per-repo), how to invoke the CLI, lab connection specifics, and known pitfalls; points to the taigun docs for the full frontmatter spec and CLI reference.
---

# Taigun ticket workflow

## What it is

`taigun` is a Python CLI that writes Taiga tickets directly to Taiga's PostgreSQL database, bypassing the Taiga API. Tickets are markdown files with YAML frontmatter; `taigun push` parses them, resolves FK references against the live DB, and inserts or updates.

## Docs first

The taigun repo's docs (`~/Development/Lab/taigun/docs/`) are the source of truth. Read the relevant page on demand rather than working from memory:

- `reference/ticket-format.md` — frontmatter fields, body structure per type, description assembly. **Read this before writing any ticket.**
- `reference/cli.md` — every command, flag, push output vocabulary, exit codes.
- `reference/state-file.md` — sidecar format, discovery walk, safe hand-edits (removing entries, fixing paths after moves).
- `guides/organising-tickets.md` — central-directory layout and anchoring rules.
- `guides/updating-tickets.md` — update, conflict, and `field: null` clearing semantics.
- `guides/milestones.md` — sprint files.

Invariants that gate most mistakes, kept inline: `type` and `project` are required; **priority is issue-only** (stories/tasks/epics note importance inline as `**Priority:** X` in the body); milestone files are frontmatter + `## Title` and nothing else; `epic:` takes the epic's Taiga **ref number**; clearing a previously-pushed field requires an explicit `field: null`.

## Where new tickets live

Per **ADR-005**: a per-user central directory, not product source repos. One subtree per project slug under `~/Tickets/`, one sidecar for everything at `~/Tickets/.taigun/state.yaml`. Ticket numbers are project-wide and monotonically increasing.

Layouts currently vary per project — taigun E1–E11 sit under `taigun/docs/epics/`, E12+ under `taigun/epics/`; vertex-play uses `docs/epics/`. Follow whatever tree the project already uses. `project:` in the frontmatter is the authoritative dispatch key; the directory path is convention for humans, never inferred by taigun.

**Do not add `docs/epics/` back into a product source repo.**

## Push workflow (lab specifics)

taigun runs natively via `uv run` — no docker for the CLI itself.

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

Every ticket carries `assignee: bmcivor` by lab convention.

If `~/Tickets/` has no sidecar yet, seed it first: `mkdir -p ~/Tickets/.taigun && touch ~/Tickets/.taigun/state.yaml`.

The project must exist on the Taiga side before any push:

```bash
uv run --project ~/Development/Lab/taigun taigun projects list
uv run --project ~/Development/Lab/taigun taigun projects create "Display Name" project-slug
```

Then push, epics first so their refs exist for story linking:

```bash
cd ~/Tickets
uv run --project ~/Development/Lab/taigun taigun push <project>/epics/*/epic.md
uv run --project ~/Development/Lab/taigun taigun push <project>/epics/*/tickets/*.md
```

**Do not use `--dry-run` against the lab.** It permanently consumes ref numbers (sequence advances survive rollback) and misreports would-be updates as inserts — taigun ticket 045 (E12). Skip dry-run until that lands.

## Updating

Edit the source file, re-push the same path — the sidecar dispatches to update. `--force` skips the conflict and missing-in-Taiga prompts. Full semantics in `guides/updating-tickets.md`.

## Pitfalls

- **Story → epic linking needs two passes.** Epic refs are assigned at push time: push epics, note the refs from the output, then set `epic: <ref>` on stories and push those.
- **Sidecar anchoring.** `locate_sidecar` walks up for an existing `.taigun/state.yaml`, then `.git/`; neither found is a loud error, fixed by seeding (above).
- **Never commit `~/Tickets/.taigun/state.yaml` to a shared remote** — per-user state, meaningless merge conflicts.
- **Watch for NULL-field bugs on new projects.** Historically (fixed as of v1.0) `projects create` left `tags_colors`, `tags`, `default_points_id`, and module flags NULL/false, crashing the Taiga API serializer. If a fresh project's UI is broken, check those columns and taiga-back logs for `dict()` / `length` errors.
- **Cross-repo edits need approval.** Editing files in another repo requires explicit confirmation from B and a fresh branch in the target repo first.

## Confirming what you wrote

Sanity-check via the Taiga UI (`http://shadowlands:9000`) or query the lab DB directly:

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
