# taigun

A CLI tool for writing tickets directly to a self-hosted [Taiga](https://taiga.io)
database.

taigun bypasses the Taiga REST API entirely and writes directly to PostgreSQL. This
means no dependency on the Taiga services being healthy, no authentication overhead,
and no rate limits.

Tickets are markdown files with a YAML frontmatter block — human-readable, diffable,
and version-controllable. See the [ticket format](reference/ticket-format.md) reference
for the file shape.

```
$ taigun push ticket.md
✓ #42 story: "Title of the ticket"
```

## The trade-off

Direct DB writes mean Django signals do not fire. taigun creates:

- No history entries (`history_historyentry`)
- No timeline entries
- No notifications (email or in-app)
- No websocket events

For the primary use case (bulk ticket creation) this is acceptable. If you need any
of the above, use the official Taiga REST API instead. The reasoning is covered in
[ADR-001](explanation/decisions/ADR-001-direct-db-writes.md).

## Compatibility

- Built and tested against **Taiga 6.9.0**
- Requires **Python 3.11+**

## Documentation

- [Ticket format](reference/ticket-format.md) — full frontmatter and body field
  reference for every ticket type
- Decisions — the ADRs behind taigun's design, under Explanation in the navigation
