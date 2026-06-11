---
gate: 1
status: passed
---

# Gate 1 — Coverage to methodology default

## Definition of done

- `loop.py` per-file coverage ≥ 95% (T01).
- `validate-event.py` per-file coverage ≥ 90% (T02).
- `lint_plan.py` per-file coverage ≥ 90% (T03).
- `_miniyaml.py` per-file coverage ≥ 90% (T04).
- `.specfuse/verification.yml`'s coverage command flipped from
  `--fail-under=70` to `--fail-under=90`; deviation comment removed; CI
  green at the new floor (T05).
- All five substantive WUs are `done`.
- `RETROSPECTIVE.md` exists; durable lessons promoted to
  `.specfuse/LEARNINGS.md`; docs and roadmap reconciled; terminal
  feature-arc verdict written (G1-CLOSE).

## Reflection notes

<Written by the human at review time.>
