# taigun

A CLI tool for writing tickets directly to a self-hosted [Taiga](https://taiga.io) database.

taigun bypasses the Taiga REST API entirely and writes directly to PostgreSQL. This means
no dependency on the Taiga services being healthy, no authentication overhead, and no
rate limits. The tradeoff is that Django signals don't fire — history entries and
notifications are not generated. For bulk ticket creation this is acceptable.

Tickets are written as markdown files with a YAML frontmatter block. The format is
human-readable and works well with version control.

## Install

```
pip install taigun
```

Requires Python 3.11+.

## Setup

```
taigun configure
```

This writes a connection profile to `~/.config/taigun/config.toml`. The database should
be reachable from your machine — the recommended approach is to expose the Postgres port
only on a VPN interface (e.g. Tailscale).

Multiple named profiles are supported if you run more than one Taiga instance:

```
taigun configure --profile work
```

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

## Usage

```
taigun push ticket.md               # push a single ticket
taigun push tickets/*.md            # push multiple tickets
taigun projects list                # list available projects
taigun epics list <project-slug>    # list epics (for linking)
taigun statuses list <project-slug> # list statuses per type
```

## Connectivity

taigun connects directly to Taiga's PostgreSQL instance. Connection details live in
`~/.config/taigun/config.toml`:

```toml
[default]
host = "100.x.x.x"
port = 5432
database = "taiga"
username = "taiga"
password = "..."
acting_user = "admin"
```

`acting_user` is the Taiga username that appears as the ticket owner on all writes.
