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
taigun push ticket.md               # push a single ticket
taigun push tickets/*.md            # push multiple tickets
taigun push --dry-run ticket.md     # parse and resolve, do not insert
```

Per-file output on success:

```
✓ #42 story: "Title of the ticket"
```

In `--dry-run` mode, the FK lookups still run against the database (so any unresolved
references are caught) but nothing is inserted:

```
~ story: "Title of the ticket"
```

If a file fails (parse error, unknown project, missing user, etc.) the error is printed
and the next file is attempted. Exit code is `0` if all succeeded, `1` if any failed.

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

### Priority

High
```

Supported types: `story`, `issue`, `task`, `epic`.

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

Releases are cut with [python-semantic-release](https://python-semantic-release.readthedocs.io/)
inside a container that mounts your local git config:

```
./scripts/release.sh version --noop   # dry run
./scripts/release.sh version          # bump, commit, tag
```

## License

MIT — see [LICENSE](LICENSE).
