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

## Ordering

```
E1 → E2 → E3 ──────────────→ E5 → E6
          E4 (parallel E3) ──┘
```

E3 and E4 can be developed in parallel once E2 is complete. Both feed into E5.
