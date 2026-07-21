# Updating tickets

Once a ticket has been pushed, its source file stays live: edit the file and
re-run `taigun push`, and taigun updates the same Taiga ticket instead of creating
a new one. The sidecar (`.taigun/state.yaml`) provides the file-to-ticket mapping;
the workflow's design is covered in
[ADR-004](../explanation/decisions/ADR-004-update-workflow.md).

## The basic loop

```
$ vim ~/Tickets/my-project/first-ticket.md
$ taigun push ~/Tickets/my-project/first-ticket.md
↺ #42 story: "Title of the ticket" (updated)
```

A file whose content hasn't changed since the last push is a no-op:

```
(unchanged) #42 story: "Title of the ticket"
```

This makes bulk pushes cheap — push a whole directory and only genuinely edited
files touch the database.

## Clearing a field

Dropping a previously-set frontmatter field is an error, not a clear:

```
✗ first-ticket.md: 'assignee' was previously set but is now absent from the
source. Add `assignee: null` to explicitly clear it.
```

Clearing requires the explicit form:

```yaml
assignee: null
```

This is deliberate — an accidental deletion in the frontmatter stays loud instead
of silently wiping the field in Taiga.

## When Taiga was edited too

If the Taiga row was modified after your last push (someone touched it in the UI),
taigun detects the drift and prompts before overwriting:

```
Taiga row for #42 story was modified at 2026-07-20T10:15:00+00:00 (after last push). Overwrite?
```

The default is **no** — declining skips the file:

```
↷ #42 story: skipped (Taiga was edited)
```

`--force` overwrites without prompting.

## When the ticket was deleted in Taiga

If the sidecar has an entry but the row is gone from Taiga, taigun prompts to
re-insert (default **yes**). The re-inserted ticket gets a **new ref**, and the
sidecar entry is updated to match:

```
✓ #57 story: "Title of the ticket" (re-inserted)
```

`--force` re-inserts without prompting.

## What you cannot change

`project` and `type` are the ticket's identity. Changing either in the frontmatter
of an already-pushed file errors loudly — taigun will not move a ticket between
projects or convert it between types. To push the file as a genuinely new ticket,
remove its entry from the sidecar first.
