# ADR-004 — Update workflow

## Status

Accepted

## Decision

taigun supports updating existing Taiga tickets by re-pushing edited markdown source files. Identification of "which Taiga ticket does this source file correspond to" is via a sidecar file (`.taigun/state.yaml`) maintained by taigun, not via a frontmatter field on the source itself.

## Reasoning

Without an update path, taigun is push-only: any edit to a ticket has to be made in the Taiga UI, after which the markdown source goes silently out of date. For any workflow where docs and tickets are meant to stay in sync — which is the primary use case for taigun — that's a fundamental hole.

The identification mechanism is the load-bearing decision. Three options were considered:

- **Frontmatter field** (`taigun_ref: 42` written back into the source file by push). Rejected — YAML serialisation libraries don't round-trip files cleanly (key order changes, comments dropped, quote styles change), producing hostile git diffs every time push runs.
- **Query Taiga first** (look up an existing ticket by subject / content / hash on each push). Rejected — Taiga's schema has no naturally stable identifier. Subjects are mutable; content hashes change with every edit; using either as a key produces duplicates on edit. Adding a marker field to Taiga to compensate is just a sidecar in a worse place.
- **Sidecar file** (separate state file tracking source path → ref). Chosen — source files stay byte-for-byte untouched by taigun, the mapping is explicit and reviewable in git, and the format is taigun's to control.

## Decisions

### Sidecar file

- **Format**: YAML.
- **Location**: `.taigun/state.yaml` at the repo root. The `.taigun/` directory is reserved for taigun-managed files (allowing future additions like cached state or logs without scattering dotfiles at the root).
- **Schema** per entry: `file_path`, `project`, `ref`, `ticket_type`, `last_pushed_at`, `content_hash`.
  - `ticket_type` saves a DB lookup on update (so we know which writer to dispatch to without re-parsing).
  - `last_pushed_at` enables the conflict check below.
  - `content_hash` enables the idempotency check below.

### Mutability

All fields are mutable except the identity triple: `project`, `type`, `ref`. That includes subject, description, status, priority (issues only — see ADR-002 update), milestone, tags, assignee, parent (tasks), epic link (stories).

Changing identity is not "an update" — it's a different ticket. If a user changes `project:` in the frontmatter, the push errors and tells them to remove the entry from the sidecar manually if they really mean to recreate elsewhere.

### Removal semantics

If a frontmatter field is present on push N and absent on push N+1, the push errors. Clearing a field requires an explicit `field: null` (or empty value) in the frontmatter.

Rationale: omission is ambiguous (did the user mean to clear it, or did they just forget?). Explicit nulls make the intent unambiguous and the failure mode loud.

### Conflict semantics

Before updating, taigun compares the Taiga row's `modified_date` to the sidecar's `last_pushed_at`. If `modified_date` is newer, someone edited the ticket via the Taiga UI since the last push.

In that case, push prompts the user: "Taiga has been edited since the last push (modified <when>). Overwrite with your local changes?" — proceed only on yes.

### Missing-ticket semantics

If the sidecar points at a ref that no longer exists in Taiga (deleted via UI), push prompts: "Sidecar references ticket #<ref> in project <slug>, which no longer exists in Taiga. Treat as new and re-insert?" — default action on yes is to insert as a new ticket and update the sidecar entry with the new ref.

### Idempotency

On push, taigun hashes the source file's content (frontmatter + body) and compares to the sidecar's stored hash. If unchanged AND the conflict check (above) is also clean, push prints `(unchanged) #<ref>` and issues no DB write.

If the hash differs OR the conflict check finds Taiga has drifted, the update proceeds (subject to the conflict prompt).

### Audit trail

Taiga's `modified_by` column on the updated row is set to the `acting_user` from config — same semantics as ticket creation. Keeps the audit trail consistent.

A dedicated `taigun` user was considered (to make "this update came from taigun" visible at a glance) but rejected as adding deployment complexity (someone has to create the user in Taiga first) for marginal value.

## Tradeoffs

- **Sidecar file is committable but doesn't have to be committed.** If a user gitignores it, every push that doesn't match an existing entry inserts as new — duplicates pile up. The cost of getting this wrong is on the user; taigun does not warn.
- **YAML library round-tripping for the sidecar is taigun's problem.** Since the sidecar's schema is taigun-controlled, we can pick a library that preserves what we need; this is not the user-facing source-file round-tripping concern that drove rejection of the frontmatter approach.
- **Prompts (conflict / missing-ticket) make push interactive.** A `--force` flag may be needed for CI / batch use cases. Decide when 034 lands and the prompt UX is in place.
- **`content_hash` ties the idempotency check to exact byte equality.** Trailing-newline changes or line-ending shifts trigger an UPDATE even though nothing meaningful changed. Acceptable for v1 of this feature; a smarter normalisation could come later if it becomes a real annoyance.
