# E7 — Integration testing & correctness

Replaces the mocked unit tests for the DB layer with integration tests against a real
Taiga schema in Docker, then fixes every bug surfaced by the now-real tests.

The mocked test suite from E1–E6 verified the SQL had the expected shape, but the
expected shape itself was wrong. v0.1.0 was published with at least three predicted
bugs that mocked tests couldn't catch. This epic closes the testing gap and corrects
the underlying writer SQL.

## Tickets

- 021 — Docker test harness
- 022 — Refactor tests to real DB with fixture utilities
- 023 — Fix bugs to green
- 024 — Jenkinsfile uses new stack

## Ordering

```
021 ─┬─→ 022 → 023
     └─→ 024
```
