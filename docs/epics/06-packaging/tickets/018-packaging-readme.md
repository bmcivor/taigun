## ~~18. Packaging and README~~ (Done)

**Epic:** E6 — Packaging & release

**As a** open source user
**I want** taigun installable via pip and documented in a README
**So that** I can use it with my own Taiga instance without reading the source

### Acceptance criteria

- `pyproject.toml` correct for PyPI publish (name, version, description, classifiers,
  license, homepage URL)
- `README.md` covers: what taigun is, install (`pip install taigun`), configure,
  push, link to `docs/ticket-format.md`
- `uv build` produces a clean wheel and sdist with no warnings
- Licence confirmed as MIT (LICENSE file present)

### Dependencies

- 017

### Blocks

- 019

### Priority

- Medium
