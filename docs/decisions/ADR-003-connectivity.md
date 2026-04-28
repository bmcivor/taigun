# ADR-003 — Database connectivity via Tailscale

## Status

Accepted

## Decision

Taiga's PostgreSQL port is exposed on the Tailscale network interface only, making
it accessible to taigun without a hand-rolled SSH tunnel or public exposure.

## Reasoning

The Taiga Docker deployment (`taiga-taiga-db-1`) does not expose port 5432 to the
host by default. Options considered:

1. **SSH tunnel** — works but requires a running SSH session and adds operational
   friction every time taigun is used.

2. **Expose on all interfaces** — simple but puts Postgres on the public network,
   which is not acceptable.

3. **Tailscale interface only** — Tailscale is already deployed on the lab box.
   Binding Postgres to the Tailscale interface restricts access to devices on the
   VPN while keeping the setup simple. No tunnel management needed.

## Implementation

A `docker-compose.override.yml` is added to the Taiga deployment (via the
`roles/taiga` Ansible role in vertex-studio) that exposes port 5432 bound to the
Tailscale interface IP:

```yaml
services:
  taiga-db:
    ports:
      - "100.x.x.x:5432:5432"
```

The Tailscale IP is templated from the Ansible inventory.

## taigun impact

Connection details (host, port, credentials) are stored in `~/.config/taigun/config.toml`.
The host value for the vertex-studio instance is the lab box's Tailscale IP.
