# Epics

Index of all epics and their ordering.

## Epic list

| Epic | Title | Tickets |
|---|---|---|
| E1 | Infrastructure & connectivity | 001–002 |
| E2 | Project scaffold | 003–004 |
| E3 | Markdown parser | 005–007 |
| E4 | DB layer | 008–014 |
| E5 | CLI | 015–017 |
| E6 | Packaging & release | 018–019 |
| E7 | Integration testing & correctness | 021–024 |

## Ordering

```
E1 → E2 → E3 ──────────────→ E5 → E6 → E7
          E4 (parallel E3) ──┘
```

E3 and E4 can be developed in parallel once E2 is complete. Both feed into E5.

E7 follows E6: the mocked-only test suite from E1–E6 didn't catch SQL bugs that
would break the writers against a real Taiga. E7 replaces those tests with
integration tests against a real Taiga schema and fixes the bugs they surface.
