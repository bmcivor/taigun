# CLI reference

Running `taigun` with no subcommand prints help. Every command that touches the
database accepts `--profile <name>` to select a connection profile; the default
profile is used when the flag is omitted.

## `taigun configure`

```
taigun configure [--profile <name>]
```

Interactive setup for a connection profile. Prompts for profile name (default
`default`), host, port (default `5432`), database (default `taiga`), username,
password (hidden), and acting user. The connection is tested before the profile is
saved to `~/.config/taigun/config.toml`; a failed test aborts with exit code 1.
Re-configuring an existing profile asks before overwriting.

## `taigun push`

```
taigun push <file>... [--dry-run] [--force] [--profile <name>]
```

Parses each file and inserts or updates the corresponding Taiga ticket. The
sidecar decides which: files with an entry are updates, files without are inserts
(see the [state file reference](state-file.md)).

| Option | Effect |
|---|---|
| `--dry-run` | Parse and resolve all FKs, then roll back instead of committing |
| `--force` | Skip the conflict and missing-in-Taiga prompts (overwrite / re-insert automatically) |
| `--profile` | Connection profile to use |

Files are processed in order; a failure prints an error and continues with the
next file.

!!! warning "`--dry-run` consumes ref numbers"
    Dry-run runs the full write path and rolls the transaction back — but
    PostgreSQL sequence advances survive rollback, so each dry-run insert
    permanently burns a ref number from the project's sequence. Real tickets
    pushed later will have gaps in their numbering. Known limitation; avoid
    dry-running against a project whose ref continuity you care about.

### Output vocabulary

One line per file:

| Output | Meaning |
|---|---|
| `✓ #42 story: "Title"` | Inserted |
| `✓ milestone: "Sprint 3"` | Inserted (milestones have no ref) |
| `(unchanged) #42 story: "Title"` | Content hash matches the sidecar — no-op |
| `↺ #42 story: "Title" (updated)` | Updated in Taiga |
| `✓ #57 story: "Title" (re-inserted)` | Was missing in Taiga; re-inserted under a new ref |
| `↷ #42 story: skipped (Taiga was edited)` | Conflict prompt declined |
| `↷ story: skipped (not in Taiga, user declined re-insert)` | Re-insert prompt declined |
| `~ story: "Title"` | Dry-run — would insert |
| `✗ file.md: <error>` | Failed (parse error, unknown project, missing user, …) |

### Exit codes

| Code | Meaning |
|---|---|
| `0` | All files succeeded (skips count as success) |
| `1` | At least one file failed |

## `taigun projects list`

```
taigun projects list [--profile <name>]
```

All projects on the instance, one per line, as `Name (slug)`.

## `taigun projects create`

```
taigun projects create <name> <slug> [--profile <name>]
```

Creates a project from the instance's default project template and prints
`Created project #<id>: <slug>`. Errors if the slug is taken. See the
[projects guide](../guides/projects.md) for what gets materialised.

## `taigun projects update`

```
taigun projects update <slug> [--name <name>] [--description <text>] [--profile <name>]
```

Updates the given fields on an existing project. At least one of `--name` /
`--description` is required. `--description ''` clears the description.

## `taigun epics list`

```
taigun epics list <project-slug> [--profile <name>]
```

All epics in a project, as `#<ref>  <subject>` — the ref is what a story's
`epic:` frontmatter field links to.

## `taigun statuses list`

```
taigun statuses list <project-slug> [--profile <name>]
```

Statuses grouped by ticket type, with closed statuses marked:

```
story:
  New
  In progress
  Done  [closed]
issue:
  ...
```

Useful before setting a `status:` frontmatter field — unknown status names fall
back to the project default with a warning rather than erroring.
