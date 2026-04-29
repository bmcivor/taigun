## ~~4. Config module~~ (Done)

**Epic:** E2 — Project scaffold

**As a** user
**I want** taigun to read connection config from `~/.config/taigun/config.toml`
**So that** I don't have to pass connection details on every command

### Acceptance criteria

- `config.py` reads and writes `~/.config/taigun/config.toml`
- Supports a `[default]` profile and named profiles under `[profiles.<name>]`
- Config fields per profile: `host`, `port`, `database`, `username`, `password`, `acting_user`
- `load_config(profile=None)` returns a typed dataclass; missing file raises a clear
  error telling the user to run `taigun configure`
- Missing required fields in an existing config raise a clear error naming the field
- Config directory created if it does not exist on first write

### Dependencies

- 003

### Blocks

- 008, 015

### Priority

- High
