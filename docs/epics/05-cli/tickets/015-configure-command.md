## ~~15. configure command~~ (Done)

**Epic:** E5 — CLI

**As a** user
**I want** `taigun configure` to walk me through setting up a connection profile
**So that** I don't have to manually edit the config file

### Acceptance criteria

- `taigun configure` prompts for: host, port (default 5432), database (default `taiga`),
  username, password, acting_user, profile name (default `default`)
- Tests the connection before saving — prints success or failure
- On success, writes to `~/.config/taigun/config.toml`
- On failure, exits with code 1 and does not save
- Re-running with an existing profile name prompts before overwriting
- `taigun configure --profile <name>` skips the profile name prompt

### Dependencies

- 004, 008

### Blocks

- 016, 017

### Priority

- High
