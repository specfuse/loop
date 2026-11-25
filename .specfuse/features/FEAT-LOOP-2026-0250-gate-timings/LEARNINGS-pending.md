<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Lessons staged for promotion — FEAT-LOOP-2026-0250

`autonomy_default: auto`, so `FEAT-LOOP-2026-0250/G1-CLOSE` may not append to
`.specfuse/LEARNINGS.md` directly (`assert_learnings_staged_under_auto`). Two entries generalize.

## Entries

- [FEAT-LOOP-2026-0250/T04] **A unit that edits `docs/*.md` must also refresh that file's packaged
  copy under `specfuse/loop/data/docs/` in the same unit.** T04 edited `docs/methodology.md` and
  not its packaged copy; its narrow tier selected no docs-sync test, so it passed, and three
  docs-sync tests went red only in the gate's broad run. Run `scripts/sync-scaffold.sh` before
  reporting, and list the packaged copy in `produces:` so the diff guard sees it.

- [FEAT-LOOP-2026-0250/T01] **A test that validates events through `validate_event` must pin the
  real packaged schemas and clear the validator's module caches.** `test_emitted_events_validate`
  passed alone and failed in the full suite because an earlier test left
  `_DRIVER_EVENT_TYPES_CACHE` empty, dropping every driver event type from the enum. Copy the
  pinning from `tests/test_event_gate_full_envelope.py` when writing the test, not after the broad
  run fails.
