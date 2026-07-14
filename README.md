# taigun

A CLI tool for writing tickets directly to a self-hosted [Taiga](https://taiga.io) database.

taigun bypasses the Taiga REST API entirely and writes directly to PostgreSQL. This means
no dependency on the Taiga services being healthy, no authentication overhead, and no
rate limits.

Tickets are written as markdown files with a YAML frontmatter block. The format is
human-readable and works well with version control.

## Compatibility

- Built and tested against **Taiga 6.9.0**
- Requires **Python 3.11+**

## Install

```
pip install taigun
```

## Setup

```
taigun configure
```

This walks you through host, port, database, credentials, and the Taiga username taigun
should act as. The connection is tested before the profile is saved. Configuration is
written to `~/.config/taigun/config.toml`.

The database needs to be reachable from your machine — the recommended approach is to
expose the Postgres port only on a VPN interface (e.g. Tailscale).

### Where to put your tickets

Ticket source files are yours to organise — taigun locates them via the paths you pass
to `push`. The recommended layout keeps them **outside your product source repos**, in
a per-user directory:

```
~/Tickets/
├── .taigun/state.yaml          <-- one sidecar tracks every project
├── project-a/
│   └── docs/epics/NN-<slug>/{epic.md, tickets/NNN-<slug>.md}
└── project-b/
    └── docs/epics/...
```

Why not in the product repo:

- Every `status:` flip, every new ticket, every completion becomes a commit in the
  product's history alongside actual code changes.
- The sidecar (`.taigun/state.yaml`) is per-user tracking state — committing it to a
  shared repo produces meaningless merge conflicts.

The sidecar is anchored automatically: `taigun push` walks up from the source file's
directory looking for an existing `.taigun/state.yaml`, then for `.git/` as a
repo-root marker. For a brand-new directory that has neither, seed the sidecar
manually so taigun knows where to put it:

```
mkdir -p ~/Tickets/.taigun && touch ~/Tickets/.taigun/state.yaml
```

### Multiple profiles

If you run more than one Taiga instance:

```
taigun configure --profile work
```

All commands accept `--profile <name>` to select which profile to use:

```
taigun push --profile work ticket.md
taigun projects list --profile work
```

The default profile is used when `--profile` is not given.

## Usage

### Pushing tickets

```
taigun push ticket.md                       # push a single ticket
taigun push tickets/*.md                    # push multiple tickets
taigun push --dry-run ticket.md             # parse and resolve, do not insert
```

Per-file output:

```
✓ #42 story: "Title"                        # newly inserted
(unchanged) #42 story: "Title"              # sidecar hash matches, no-op
↺ #42 story: "Title" (updated)              # content changed, updated in Taiga
↷ #42 story: skipped (Taiga was edited)     # conflict — re-run with --force to overwrite
~ story: "Title"                            # dry-run: would push
```

Once a ticket has been pushed, editing the source file and re-running `taigun push`
updates the same Taiga row (looked up via the sidecar). Dropping a previously-set
frontmatter field errors — clearing requires an explicit `field: null` so accidental
deletions are loud.

If a file fails (parse error, unknown project, missing user, etc.) the error is printed
and the next file is attempted. Exit code is `0` if all succeeded, `1` if any failed.

`--force` skips conflict / missing-in-Taiga prompts (overwrite / re-insert automatically).

### Listing

```
taigun projects list                # all projects on the instance
taigun epics list <project-slug>    # all epics in a project
taigun statuses list <project-slug> # statuses per ticket type
```

Useful for looking up a project slug or checking which statuses exist before writing a
ticket.

## Ticket format

Tickets are markdown files with a YAML frontmatter block:

```markdown
---
type: story
project: my-project-slug
assignee: blake
tags: backend, auth
---

## Title of the ticket

**As a** developer
**I want** a thing
**So that** it works

### Acceptance criteria

- criterion one
- criterion two
```

Supported types: `story`, `issue`, `task`, `epic`, `milestone`. `### Priority` is issue-only — it errors on any other ticket type. Milestones are minimal (frontmatter + `## Title` only) — see `docs/ticket-format.md`.

See [docs/ticket-format.md](docs/ticket-format.md) for the full field reference.

## Configuration file

Connection details live in `~/.config/taigun/config.toml`:

```toml
[default]
host = "100.x.x.x"
port = 5432
database = "taiga"
username = "taiga"
password = "..."
acting_user = "admin"

[profiles.work]
host = "..."
port = 5432
database = "taiga"
username = "taiga"
password = "..."
acting_user = "blake"
```

`acting_user` is the Taiga username that appears as the ticket owner on all writes.

## What taigun does not do

Direct DB writes mean Django signals do not fire. As a result:

- No history entries (`history_historyentry`)
- No timeline entries
- No notifications (email or in-app)
- No websocket events

For the primary use case (bulk ticket creation) this is acceptable. If you need any of
the above, use the official Taiga REST API instead.

## Development

Tests run inside Docker:

```
docker compose run --rm test
```

Releases are cut from the `tag-release` branch using
[python-semantic-release](https://python-semantic-release.readthedocs.io/) inside a
container that passes your local git identity through:

```
git checkout tag-release
./scripts/release.sh --noop version --minor   # dry run
./scripts/release.sh version --minor          # bump, commit, tag
git push origin tag-release --tags
```

The `--minor` (or `--major` / `--patch`) flag forces a bump level. Drop it to let
semantic-release determine the bump from conventional commit messages since the last
tag. `--noop` is a global flag and must come before the `version` subcommand.

## License

MIT — see [LICENSE](LICENSE).
