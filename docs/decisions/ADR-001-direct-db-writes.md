# ADR-001 — Direct DB writes over API wrapper

## Status

Accepted

## Decision

taigun writes tickets directly to Taiga's PostgreSQL database rather than calling
the Taiga REST API.

## Reasoning

The Taiga REST API already exists. A CLI that wraps it adds a thin layer over
something the user could already do with curl — not a compelling open source tool.

Direct DB writes offer things the API does not:
- Works when Taiga services are down or unhealthy
- No authentication token management
- Suitable for bulk imports without rate limiting concerns
- Direct control over every field

## Tradeoffs

Django signals do not fire on direct inserts, so the following are not generated:

- History / activity log entries on tickets
- Email notifications to watchers
- Real-time websocket events (board does not auto-refresh)
- Webhook calls

For the primary use case (AI-assisted ticket creation, bulk import) none of these
are considered load-bearing. Tickets appear correctly on the board and are fully
functional once the page is loaded.

## What we must handle manually

Because we bypass the ORM, taigun is responsible for:

- Setting `created_date` and `modified_date` explicitly
- Setting `version = 1` (required by Django's OCCModelMixin)
- Allocating `ref` via the project's Postgres sequence and writing to
  `references_reference`
