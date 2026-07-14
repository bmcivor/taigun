# ADR-005 — Central ticket directory

## Status

Accepted

## Decision

taigun-managed ticket source files live in a single per-user central directory tree, separate from any product's source repo. The intended layout is:

```
~/Tickets/                       <-- git repo root
├── .git/
├── .taigun/state.yaml           <-- one sidecar for every project
├── taigun/
│   └── docs/epics/...
├── vertex-play/
│   └── docs/epics/...
└── vertex-studio/
    └── docs/epics/...
```

Each product source repo (e.g. `Lab/taigun/`) is stripped of its `docs/epics/` tree. `docs/` in the source repo continues to hold project-level documentation — READMEs, ADRs about the product, design notes suitable for mkdocs / sphinx generation.

## Reasoning

Two things go wrong when taigun-managed tickets live in the product's source repo:

1. **Product history is polluted with ticket-tracking noise.** Every `status:` flip, every new ticket, every "resolved" edit becomes a commit in the product repo. The blame log for the actual code gets buried under process churn, and PR reviewers cannot separate "code change" from "ticketing paperwork" without visually filtering commits.
2. **taigun's state is per-user, not per-repo.** The sidecar (`.taigun/state.yaml`) records what a specific developer has pushed. It is meaningless to another contributor and produces merge conflicts on any shared branch. Committing user-tracking state into a shared repo is a category error.

Consolidating into one per-user Tickets repo fixes both:

- Product repo history stays about product changes.
- One sidecar tracks every project, one file to inspect for drift.
- `taigun push` already resolves each file's target project from its `project:` frontmatter, so multi-project batches from a single tree work without code changes.

The alternative — a per-user gitignored ticket directory inside each product repo — was rejected because it splits state across N locations for no gain, requires configuring the skill per repo, and still ships the product repo with a taigun-shaped hole.

## Decisions

### Layout

- **Repo root**: `~/Tickets/` by convention; the location is user-chosen and not enforced by taigun. `locate_sidecar` (per 036) anchors the sidecar to `.git/` at whatever directory the user cares to run push from.
- **Per-project sub-directory**, named after the Taiga project slug: `~/Tickets/taigun/`, `~/Tickets/vertex-play/`, etc.
- **Inside each sub-directory**, the existing `docs/epics/<NN>-<kebab-name>/{epic.md, tickets/<NNN>-*.md}` structure is preserved unchanged — no restructuring of the ticket tree itself.
- **Sidecar**: `~/Tickets/.taigun/state.yaml`. One file, all projects. Entries store paths relative to the repo root, so they look like `taigun/docs/epics/01-infrastructure/epic.md`.

### Frontmatter

`project:` in each ticket's frontmatter remains required and remains the authoritative dispatch key. Directory location is a filesystem convention for humans to navigate; it is not a taigun contract. A file with `project: taigun` in it pushes to Taiga project `taigun` regardless of which sub-directory it happens to be under.

### Migration approach

- Per source repo, `git mv docs/epics/` out to `~/Tickets/<slug>/docs/epics/`, then commit the removal in the source repo.
- Delete the corresponding Taiga project on the lab; recreate and push from the new location. Sidecar is not migrated in-place because the existing sidecar has content-hashes tied to (now-moved) paths and would be more work to fix up than to regenerate.
- Ordering: ADR-005 accepted first, then each project migrated one at a time in its own PR against its own source repo. This ADR only prescribes the destination; each source repo controls the timing of its own move.

### Not enforced by taigun

- The `~/Tickets/` path itself. taigun continues to use `locate_sidecar` walk-up; the user can point that at any directory that is a git repo.
- Whether every product ships without a `docs/epics/`. Some repos may keep tickets in-tree for reasons unrelated to taigun (e.g. archived projects). taigun does not care where the source lives.

### Out of scope

- Migrating tickets in vertex-play / vertex-block / vertex-studio — each of those is owned by its own repo and gets a mechanical move ticket there.
- Any change to the update workflow described in ADR-004. Sidecar semantics, mutability, conflict detection, and the identity triple all stand.
- A `taigun` CLI change to help with the migration itself. Migration is a one-shot `git mv` per repo; a helper would be more code than the move.
