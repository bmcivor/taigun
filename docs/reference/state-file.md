# State file (sidecar)

The sidecar, `.taigun/state.yaml`, is taigun's record of which source files have
been pushed and what they became in Taiga. It is what lets `push` dispatch to
insert vs update. It is per-user tracking state — see
[ADR-004](../explanation/decisions/ADR-004-update-workflow.md) for why it exists
and [ADR-005](../explanation/decisions/ADR-005-central-ticket-directory.md) for
why it should not live in a shared product repo.

## Location and discovery

The sidecar sits in a `.taigun/` directory at the root of your ticket tree. On
each non-dry-run push, taigun walks up from the first source file's directory:

1. The first existing `.taigun/state.yaml` found wins.
2. Otherwise, the nearest ancestor containing `.git/` is taken as the root, and
   the sidecar is created there on first save.
3. If neither exists, push errors — seed the root explicitly with
   `mkdir -p <root>/.taigun && touch <root>/.taigun/state.yaml`.

## Format

```yaml
entries:
- file_path: my-project/docs/epics/01-infra/tickets/001-connectivity.md
  project: my-project-slug
  ref: 42
  ticket_type: story
  last_pushed_at: '2026-07-20T10:15:00Z'
  content_hash: sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
```

| Field | Meaning |
|---|---|
| `file_path` | Source file path, relative to the sidecar's root, forward slashes |
| `project` | Project slug at push time — identity, changing it in the source errors |
| `ref` | Taiga ref number the file pushed as |
| `ticket_type` | `story` / `issue` / `task` / `epic` / `milestone` — also identity |
| `last_pushed_at` | UTC timestamp of the last push; compared against Taiga's `modified_date` for conflict detection |
| `content_hash` | `sha256:` + hex digest of the file's raw bytes; a match makes re-push a no-op |

All six fields are required. Entries are kept sorted by `file_path`; the file is
rewritten once at the end of each push.

## Strict loading

A missing sidecar is treated as empty, but a broken one is never silently
repaired: malformed YAML, a duplicate `file_path`, or an entry missing required
fields all abort the push with an error. Drift in tracking state compounds
quietly, so failures are loud by design.

## Hand-editing

The sidecar is plain YAML and safe to edit deliberately:

- **Remove an entry** to make taigun treat its source file as never pushed — the
  next push inserts a new ticket (this is the escape hatch for changing a
  ticket's `project` or `type`).
- **Rewrite `file_path` values** after moving or renaming source files, so
  entries follow their files instead of being orphaned.
