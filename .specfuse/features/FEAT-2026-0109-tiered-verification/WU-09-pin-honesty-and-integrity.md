---
id: FEAT-2026-0109/T09
type: implementation
status: pending
attempts: 0
planned_cost_usd: 4.00
oracle_env: macos_local
produces_driver_helper: format_driver_staleness_warning
produces:
  - specfuse/loop/loop.py
  - specfuse/loop/build_provenance.py
  - tests/test_pin_honesty_and_integrity.py
duration_seconds: 756.228
cost_usd: 1.887924
input_tokens: 94
output_tokens: 42841
---

# A pinned run says what it actually does, and never trusts a half-reaped pin

**Objective.** Close the two criteria gate 3's close recorded as unmet
(`FOLLOW-UPS.md`, issues #3270 and #3271): the pinned branch must print
pin-aware text where it declines to halt, and `materialize_pin` must validate a
pin's **content** before reusing it.

**Context.** FEAT-2026-0109/T09; read `FOLLOW-UPS.md` first — both entries carry
the criterion verbatim, the command run, and an explicit re-run condition. This
unit exists because the terminal close recorded `not_met` and a fresh judge
agreed, unlowered. T08's mechanism is sound and stays: pinning works, and gate
3's restart count was exactly 1 as predicted. What is wrong is what the driver
*says* and what it *trusts*.

**Defect 1 — the driver says the opposite of what it does.** At the seam where a
pinned run declines to halt it prints the unpinned text: "STALE DRIVER
PROCESS … A fresh driver process is required before any of these can be trusted
as a verification of the change." It then does not halt and dispatches the next
unit. `format_driver_staleness_warning(wu_id, driver_paths)` takes no pin
argument, so one string serves both branches, and the gate-completion summary
has the same shape. This violates `GATE-03.md`'s own bullet: *"The driver says
so, in words, at the point where it declines to halt — an operator must never
have to infer from silence which build verified their gate."* They are not left
inferring from silence; they are told the opposite.

**Defect 2 — a partially reaped pin is still trusted.** `materialize_pin` reuses
a pin whenever `.specfuse-pin-tree` matches the directory name, checking nothing
else, and writes into `tempfile.gettempdir()` with `shutil.copytree`, which
preserves source mtimes — so a freshly written pin already looks days old to an
age-based tmp reaper. A pin missing files is still reported as the running
build. That is #1040's "confidently wrong" failure mode reintroduced by the
mechanism built to retire it, which is why it outranks defect 1.

**Incremental edit.** T08 delivered both files. This unit adds a pin-aware
branch to the staleness text and a content check to `materialize_pin`; it
changes nothing about when the halt fires, the marker's meaning, or
`_reexec_pinned`'s re-exec.

**Do not weaken the unpinned path.** Its wording, event and exit code 3 stay
byte-for-byte. `UnpinnedRunStillHalts` must pass untouched — that escape hatch
is what makes retiring the halt defensible at all.

**Acceptance criteria.**

- `tests/test_pin_honesty_and_integrity.py::test_pinned_seam_prints_pin_aware_text` fails on HEAD and passes after: driving the pinned-driver scenario as a subprocess and reading its **stdout**, the per-unit seam names the pin's tree hash and the tree the edit takes effect in (`next_pin_tree`, already computed at the seam and written to the event), and states that this process continues against its snapshot. Asserted on stdout, because the gate oracle is bound to `events.jsonl` and the exit code and cannot see this.
- `::test_gate_summary_is_pin_aware_too`: the gate-completion summary carries the same distinction — the follow-up found both surfaces sharing one string.
- `::test_unpinned_text_is_byte_identical`: the unpinned branch's warning and summary are unchanged from HEAD, compared as strings.
- `::test_a_reaped_pin_is_rebuilt_not_reused`: materialize a pin, delete a file inside it behind the driver's back (e.g. `specfuse/loop/__init__.py`), call `materialize_pin` again, and assert the returned pin is **complete** — not the mutilated directory.
- `::test_a_reused_pin_resolves_the_pin_not_the_working_tree`: a launcher-shaped import inside a reused pin resolves `specfuse.loop.loop` to the pin, never to the working tree.
- `python3 -m unittest tests.test_installed_copy_driver_e2e tests.test_driver_restart_halt_wiring tests.test_pin_marker_not_inherited -q` reports `OK` — T08's oracle and the halt/marker guarantees are undisturbed.
- `python3 -m unittest discover -s tests -q` reports `OK`, and `bash scripts/smoke-test.sh` exits 0.

**Do not touch.** When the halt fires (T08's predicate); `PINNED_BUILD_ENV_VAR`'s
meaning or the `child_env_without_pin_marker` strip; gates 1 and 2's mechanisms;
`.specfuse/verification.yml`; `.git/`, secrets.

**Verification.** The narrow tier for `implementation`, plus this gate's
`feature_oracle`.

**Escalation triggers.** Emit `status: blocked` if fixing defect 2 cannot be
done without moving pins out of `tempfile.gettempdir()` — relocating the cache
and choosing a retention policy is a design decision for an operator, and
`FOLLOW-UPS.md` offers it as an alternative ("and/or"), not a requirement. Also
block if a pin-aware message cannot be produced without changing when the halt
fires; the message is this unit's scope, the predicate is not.
</content>
