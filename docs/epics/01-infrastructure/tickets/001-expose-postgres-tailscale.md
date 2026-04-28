## 1. Expose Postgres over Tailscale and pin Taiga version in vertex-studio

**Epic:** E1 — Infrastructure & connectivity

**As a** taigun developer
**I want** Taiga's Postgres port accessible over Tailscale and the Taiga version pinned
**So that** taigun can connect to the database without an SSH tunnel, and schema-breaking
upgrades cannot happen without a deliberate version bump

### Context

`taiga-taiga-db-1` runs `postgres:12.3` but does not expose port 5432 to the host.
The lab box already has Tailscale deployed. The fix is a `docker-compose.override.yml`
deployed by the `roles/taiga` Ansible role in vertex-studio, binding 5432 to the
Tailscale interface IP only.

The Tailscale IP should be templated from the Ansible inventory rather than hardcoded.

The Taiga images currently use `:latest` tags. taigun writes directly to the DB schema,
so an unannounced Taiga upgrade can silently break inserts. All Taiga image tags should
be pinned to explicit versions in `inventory/group_vars/all/vars.yaml` and referenced
from the role, matching the same approach used for other services in vertex-studio.

### Acceptance criteria

- `roles/taiga` in vertex-studio deploys a `docker-compose.override.yml` that binds
  port 5432 to the lab box's Tailscale IP
- Port is not bound on `0.0.0.0` — Tailscale interface only
- All Taiga image tags (`taiga-back`, `taiga-front`, `taiga-events`, `taiga-protected`)
  pinned to explicit versions in `vars.yaml` — no `:latest` tags remaining
- Pinned versions match what is currently running on the lab box (`docker inspect` to
  confirm image digests)
- Taiga services remain healthy after the change (`docker compose ps` all Up)
- Change is on its own branch in vertex-studio, not mixed into other work

### Dependencies

- None

### Blocks

- 002

### Priority

- High
