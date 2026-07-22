# taigun

A CLI tool for writing tickets directly to a self-hosted [Taiga](https://taiga.io)
database.

taigun bypasses the Taiga REST API entirely and writes directly to PostgreSQL. This
means no dependency on the Taiga services being healthy, no authentication overhead,
and no rate limits.

Tickets are written as markdown files with a YAML frontmatter block. The format is
human-readable and works well with version control.

## Compatibility

- Built and tested against **Taiga 6.9.0**
- Requires **Python 3.11+**

## Install

```
pip install taigun
```

## Quick start

```
taigun configure
```

This walks you through host, port, database, credentials, and the Taiga username
taigun should act as. The connection is tested before the profile is saved. The
database needs to be reachable from your machine — the recommended approach is to
expose the Postgres port only on a VPN interface (e.g. Tailscale).

Write a ticket:

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

Push it:

```
$ taigun push ticket.md
✓ #42 story: "Title of the ticket"
```

Editing the file and pushing again updates the same Taiga ticket — no duplicates.
Supported types: `story`, `issue`, `task`, `epic`, `milestone`.

```
taigun projects list                # look up project slugs
taigun epics list <project-slug>    # epic refs for linking
taigun statuses list <project-slug> # statuses per ticket type
```

## What taigun does not do

Direct DB writes mean Django signals do not fire: no history entries, no timeline
entries, no notifications, no websocket events. For the primary use case (bulk
ticket creation) this is acceptable. If you need any of the above, use the official
Taiga REST API instead.

## Documentation

Full documentation — getting started, guides, and the complete ticket-format and
CLI references — lives in [docs/](docs/), served with mkdocs:

```
docker compose up docs    # http://localhost:8000
```

## License

MIT — see [LICENSE](LICENSE).
