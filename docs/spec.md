# taigun — specification

## What it is

A CLI tool that parses markdown-formatted ticket files and writes them directly to a
Taiga PostgreSQL database. Supports user stories, issues, tasks, and epics.

Designed to be generic — works with any self-hosted Taiga instance.

## What it is not

A wrapper around the Taiga REST API. taigun writes directly to the database, bypassing
the API layer entirely. This means no dependency on the Taiga services being healthy,
and no authentication overhead.

The tradeoff: Django signals do not fire, so history entries, notifications, and
real-time websocket events are not generated. For the primary use case (bulk ticket
creation) this is acceptable.

## Connectivity

taigun connects to Taiga's PostgreSQL instance directly. The database is not expected
to be publicly exposed — the recommended approach is to restrict access to a VPN
(e.g. Tailscale) and expose the Postgres port only on that interface.

Connection details are stored in a config file at `~/.config/taigun/config.toml`.
Multiple named profiles are supported for users running more than one Taiga instance.

## CLI

```
taigun configure                    # interactive setup, writes config file
taigun push <file>                  # push a single ticket file
taigun push <glob>                  # push multiple ticket files
taigun projects list                # list projects available on the configured instance
taigun epics list <project-slug>    # list epics in a project (for linking)
taigun statuses list <project-slug> # list statuses per type in a project
```

## Project structure

```
taigun/
├── pyproject.toml
├── taigun/
│   ├── __init__.py
│   ├── cli.py          # typer entry point
│   ├── config.py       # config file read/write (~/.config/taigun/config.toml)
│   ├── parser.py       # markdown → TicketModel dataclass
│   ├── models.py       # dataclasses: Story, Issue, Task, Epic
│   ├── db.py           # postgres connection + insert logic
│   └── resolver.py     # lookup IDs for project, status, priority, type, severity
```

## DB write logic

For each ticket type, the write sequence is:

1. Resolve project slug → `project_id`
2. Resolve FK lookups: `status`, `priority`, `type`, `severity` → IDs (per project)
3. Resolve `owner` user ID from config (the user taigun acts as)
4. Get next ref number: `SELECT nextval('references_projectN')` where N = project_id
5. Insert the ticket row with `ref`, `created_date`, `modified_date` set explicitly
6. Insert a row into `references_reference` linking the ref to the new object

Step 4–6 must run in a single transaction.

### Tables written per ticket type

| Type | Primary table | Notes |
|---|---|---|
| User story | `userstories_userstory` | M2M `userstories_userstory_assigned_users` if assignees set |
| Issue | `issues_issue` | |
| Task | `tasks_task` | FK to `userstories_userstory` if parent story set |
| Epic | `epics_epic` | |

### Fields set on every insert

- `created_date` — current timestamp (UTC)
- `modified_date` — current timestamp (UTC)
- `ref` — next value from project sequence
- `version` — `1` (OCC version field, required by Django's OCCModelMixin)

### Fields intentionally not set

- History entries (`history_historyentry`) — not written
- Timeline entries (`timeline_timeline`) — not written
- Notifications — not triggered
- `epics_relateduserstory` — not written unless epic linking is explicitly requested

## Configuration file format

```toml
[default]
host = "100.x.x.x"
port = 5432
database = "taiga"
username = "taiga"
password = "..."
acting_user = "admin"   # Taiga username that appears as ticket owner

[profiles.my-other-instance]
host = "..."
...
```

## Packaging

- Python package, managed with `uv`
- Entry point: `taigun` command
- Installable via `pip install taigun` (PyPI target)
- Minimum Python version: 3.11
