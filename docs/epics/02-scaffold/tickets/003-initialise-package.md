## 3. Initialise Python package

**Epic:** E2 — Project scaffold

**As a** developer
**I want** the project scaffolded with pyproject.toml and the taigun package structure
**So that** I can start writing modules against a known foundation

### Acceptance criteria

- `pyproject.toml` present with:
  - Package name `taigun`, version `0.1.0`
  - Dependencies: `typer`, `psycopg2-binary`, `python-frontmatter`, `tomli` (Python < 3.11 compat via `tomllib` stdlib otherwise)
  - Entry point: `taigun = "taigun.cli:app"`
  - Minimum Python: `3.11`
- `uv.lock` committed
- Package structure in place:
  ```
  taigun/
  ├── __init__.py
  ├── cli.py
  ├── config.py
  ├── models.py
  ├── parser.py
  ├── db.py
  └── resolver.py
  ```
- `taigun --help` runs without error (stub CLI is fine)

### Dependencies

- None

### Blocks

- 004, 005, 006, 007, 008

### Priority

- High
