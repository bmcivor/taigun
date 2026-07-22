# Configuration

Connection profiles live in `~/.config/taigun/config.toml`. The file is created by
`taigun configure` and read on every command; editing it by hand works too.

## File shape

```toml
[default]
host = "100.x.x.x"
port = 5432
database = "taiga"
username = "taiga"
password = "..."
acting_user = "admin"

[profiles.work]
host = "..."
port = 5432
database = "taiga"
username = "taiga"
password = "..."
acting_user = "blake"
```

The `[default]` table is the profile used when `--profile` is not given; named
profiles live under `[profiles.<name>]`.

## Fields

All six fields are required on every profile.

| Field | Description |
|---|---|
| `host` | PostgreSQL host — the database server, not the Taiga web address |
| `port` | PostgreSQL port |
| `database` | Database name (`taiga` on a standard install) |
| `username` | PostgreSQL user |
| `password` | PostgreSQL password |
| `acting_user` | Taiga username set as the owner on everything taigun writes |

!!! note
    The password is stored in plain text — keep the file's permissions restricted
    to your user.

## Errors

- Missing file: taigun exits with a pointer to run `taigun configure`.
- Unknown profile name: exits naming the profile it looked for.
- Profile missing required fields: exits listing the missing field names.
