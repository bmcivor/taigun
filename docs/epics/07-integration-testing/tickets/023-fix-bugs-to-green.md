## 23. Fix bugs to green

**Epic:** E7 — Integration testing & correctness

**As a** developer
**I want** every integration test passing against the real `test-db`
**So that** the writers actually work end-to-end against a real Taiga schema and a
0.1.1 release can be cut with confidence

### Acceptance criteria

- Every test in the suite passes against `test-db`
- Every failure surfaced by the now-real test suite is fixed (rather than worked
  around or skipped)
- No tests marked `xfail` or skipped to make the suite green

### Context

The schema audit predicted at least three failures in v0.1.0 (story `priority_id`,
`epics_relateduserstory.order`, `references_reference.created_at`) plus tags being
silently dropped. Until the integration tests run, the actual count is unknown. Scope
is "make them all pass", not enumerate fixes in advance.

### Dependencies

- 022

### Blocks

- (gates a 0.1.1 release)

### Priority

- High
