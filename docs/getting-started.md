# Getting started

This walks you from a fresh install to your first ticket landing in Taiga.

## Prerequisites

- Python 3.11+
- A self-hosted Taiga instance (built and tested against **6.9.0**)
- Network access to Taiga's PostgreSQL port

!!! note "Database reachability"
    taigun connects to Postgres directly, so the database must be reachable from
    your machine. The recommended approach is to expose the Postgres port only on
    a VPN interface (e.g. Tailscale) — see
    [ADR-003](explanation/decisions/ADR-003-connectivity.md) for the reasoning.

## 1. Install

```
pip install taigun
```

## 2. Configure a connection

```
taigun configure
```

This prompts for the profile name (default `default`), host, port, database,
credentials, and the **acting user** — the Taiga username that appears as the owner
on everything taigun writes. The connection is tested before the profile is saved
to `~/.config/taigun/config.toml`.

Verify it works:

```
$ taigun projects list
My Project (my-project-slug)
```

If you don't have a project yet, create one:

```
$ taigun projects create "My Project" my-project-slug
Created project #1: my-project-slug
```

## 3. Set up a ticket directory

Ticket source files live in a per-user directory, outside your product source repos:

```
mkdir -p ~/Tickets/.taigun && touch ~/Tickets/.taigun/state.yaml
```

The empty `state.yaml` anchors the **sidecar** — the file taigun uses to remember
which source files map to which Taiga tickets. Without it (or a `.git/` directory),
`taigun push` refuses to run rather than guess where tracking state belongs.

## 4. Write a ticket

Create `~/Tickets/my-project/first-ticket.md`:

```markdown
---
type: story
project: my-project-slug
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

The frontmatter carries the machine-readable fields, the body becomes the ticket's
description. The full field reference for every ticket type is in
[Ticket format](reference/ticket-format.md).

## 5. Push it

```
$ taigun push ~/Tickets/my-project/first-ticket.md
✓ #1 story: "Title of the ticket"
```

The ticket is now in Taiga under `my-project-slug`, and the sidecar has recorded
the mapping. Editing the file and re-running `taigun push` updates the same Taiga
ticket instead of creating a duplicate.
