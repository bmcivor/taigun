# Organising tickets

taigun does not dictate where ticket files live — `push` takes whatever paths you
give it. This guide covers the recommended layout and how the sidecar anchors to it.

## The central ticket directory

Keep ticket sources in a single per-user directory, **outside your product source
repos**, with one subtree per project:

```
~/Tickets/
├── .taigun/state.yaml          <-- one sidecar tracks every project
├── project-a/
│   └── docs/epics/NN-<slug>/{epic.md, tickets/NNN-<slug>.md}
└── project-b/
    └── docs/epics/...
```

The `epics/` structure within each project is convention, not requirement — taigun
only cares about the paths you pass to `push`. The reasoning behind the central
directory is covered in
[ADR-005](../explanation/decisions/ADR-005-central-ticket-directory.md).

## Why not in the product repo

- Every `status:` flip, every new ticket, every completion becomes a commit in the
  product's history alongside actual code changes.
- The sidecar (`.taigun/state.yaml`) is per-user tracking state — committing it to
  a shared repo produces meaningless merge conflicts.

You can `git init` the central directory itself if you want local history over your
tickets; taigun works the same either way.

## How the sidecar anchors

On every (non-dry-run) push, taigun walks up from the first source file's directory
to find where tracking state lives:

1. The first existing `.taigun/state.yaml` wins.
2. Otherwise, the nearest ancestor containing `.git/` becomes the root, and the
   sidecar is created there on first push.
3. If neither is found, the push errors rather than guessing.

For a brand-new directory with neither marker, seed the sidecar manually:

```
mkdir -p ~/Tickets/.taigun && touch ~/Tickets/.taigun/state.yaml
```

All files in a single `push` invocation are expected to live under the same root —
the sidecar is located once, from the first file.

## Renaming or moving ticket files

The sidecar maps tickets by **path relative to its own directory**. Moving or
renaming a pushed source file orphans its entry — the file's new path has no
mapping, so the next push inserts a duplicate ticket instead of updating.

!!! warning "Moving pushed files"
    If you reorganise, update the `file_path` values in `.taigun/state.yaml` to
    match the new locations before pushing again. Content hashes are unaffected
    by moves, so a follow-up push should report `(unchanged)` for every moved
    file.
