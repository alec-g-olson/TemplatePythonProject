104: Stabilize Flaky CI Test for Sleep and mtime
===============================================

Overview
--------
This bugfix resolves a flaky GitHub CI/CD failure where short ``sleep`` calls and
filesystem ``mtime`` updates were not reliably ordered across environments.

Requirements
------------
- Make the timestamp-based unit test deterministic in CI so reruns are no longer needed
  for this known sleep/mtime timing issue.

Acceptance Criteria / Feature Tests
-----------------------------------
- CI no longer intermittently fails due to sleep/mtime timing in this test path.
- No new feature test is required because this is an internal flaky-test stabilization
  fix rather than end-user behavior.
