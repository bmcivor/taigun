## 24. Jenkinsfile uses new test stack

**Epic:** E7 — Integration testing & correctness

**As a** developer
**I want** Jenkins on the lab box to run the same docker-compose stack as local dev
**So that** CI behaves identically and there's no Jenkins-specific config to maintain

### Acceptance criteria

- `Jenkinsfile` updated to bring up `test-db` + `test-db-init`, run the test suite
  against them, and tear down after
- Same `docker compose` invocation works locally and on the lab Jenkins agent — no
  alternate compose file or Jenkins-specific flags
- Pipeline cleans up containers and volumes on success and failure

### Dependencies

- 021

### Blocks

- None

### Priority

- Medium
