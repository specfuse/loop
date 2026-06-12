---
gate: 1
status: awaiting_review
---

# Gate 1 — integration_workspace deterministic, 50× audit passes

## Definition of done

- `tests/test_driver_integration.py::integration_workspace` exits
  cleanly with explicit fd hygiene (no leaked subprocess handles, no
  leaked lock fds, no in-flight git background tasks at teardown).
- `tests/test_driver_integration.py` runs 50× in a loop locally with
  zero `OSError: Directory not empty` failures.
- API of `integration_workspace` unchanged (`@contextmanager` yielding
  a `Path`).
- `RETROSPECTIVE.md` exists, durable lessons (if any) are in
  `.specfuse/LEARNINGS.md`, `PLAN.md` and roadmap row reflect `done`.

Single-gate feature: combined `close` ceremony (`G1-CLOSE`)
substitutes for the four-WU closing sequence. No `plan-next` — no
successor gate. The close session re-runs the 50× audit one more
time as a final oracle.

## Reflection notes

<Written by the human at review time.>
