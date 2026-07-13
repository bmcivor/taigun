---
type: story
project: taigun
status: Done
---

## 36. Sidecar defaults to first source file's parent, breaks multi-directory push

**As a** taigun user pushing tickets from multiple subdirectories in one command
**I want** the sidecar to land at the actual repo root, not under whichever
subdirectory the first source file happens to live in
**So that** the first push into a fresh repo doesn't reject every file that
isn't a sibling of the first one

### Context

Found by the 025 dog-food pass on 2026-07-13. Ran:

```
uv run taigun push docs/epics/*/epic.md docs/epics/*/tickets/*.md
```

Two files pushed. Every subsequent file errored with:

```
Source file PosixPath('docs/epics/02-scaffold/epic.md') is not inside the
sidecar's repo root (…/docs/epics/01-infrastructure); cannot compute relative path
```

Root cause is in `taigun/state.py::locate_sidecar` — when no existing
`.taigun/state.yaml` is found on the walk-up, it returns
`start / SIDECAR_DIR_NAME / SIDECAR_FILE_NAME`. `start` comes from
`Path(files[0]).resolve().parent` in `taigun/cli.py`, i.e. the first source
file's directory. So the sidecar lands under
`docs/epics/01-infrastructure/.taigun/`, and every file outside that subtree
fails `_to_relative`.

### Proposed fix

Extend `locate_sidecar` so that when no existing `.taigun/state.yaml` is found
on the walk-up, it walks up a second time looking for a repo marker
(`.git/` — extend to others later if needed). If found, default the sidecar
to `<repo-root>/.taigun/state.yaml`. If neither an existing sidecar nor a
`.git/` is found on the walk-up, raise a clear error instructing the user to
`mkdir .taigun` at their intended repo root — better a loud stop than a
silent misplacement.

### Acceptance criteria

- Pushing multiple files from different subdirectories under a repo that has
  `.git/` but no `.taigun/` places the sidecar at `<repo-root>/.taigun/state.yaml`
  and every file in the batch succeeds
- If neither `.taigun/` nor `.git/` is found on the walk-up, taigun errors
  clearly and refuses to place the sidecar
- Regression test added in `tests/test_state.py::TestLocateSidecar`

### Dependencies

- 033 (introduced the bug)
