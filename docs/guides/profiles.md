# Multiple profiles

A profile bundles a database connection with an acting user. One profile per Taiga
instance is the usual setup; two profiles pointing at the same instance under
different acting users also works.

## Creating a named profile

```
taigun configure --profile work
```

Same interactive setup as the default profile — the connection is tested before
anything is saved. Re-configuring an existing profile asks before overwriting.

## Using a profile

Every command accepts `--profile`:

```
taigun push --profile work ticket.md
taigun projects list --profile work
```

When `--profile` is not given, the default profile (created by a plain
`taigun configure`) is used.

## On disk

Profiles live in `~/.config/taigun/config.toml` — the default profile under
`[default]`, named ones under `[profiles.<name>]`:

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

`acting_user` is the Taiga username that appears as the owner on everything taigun
writes through that profile.
