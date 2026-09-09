### tests: PASS
```
$ python3 -m unittest tests.test_pin_honesty_and_integrity -v -b
test_gate_summary_is_pin_aware_too (tests.test_pin_honesty_and_integrity.PinnedSeamAndSummaryArePinAware.test_gate_summary_is_pin_aware_too) ... ok
test_pinned_seam_prints_pin_aware_text (tests.test_pin_honesty_and_integrity.PinnedSeamAndSummaryArePinAware.test_pinned_seam_prints_pin_aware_text) ... ok
test_process_exit_code_is_clean (tests.test_pin_honesty_and_integrity.PinnedSeamAndSummaryArePinAware.test_process_exit_code_is_clean) ... ok
test_a_reaped_pin_is_rebuilt_not_reused (tests.test_pin_honesty_and_integrity.ReapedPinIsRebuiltNotReused.test_a_reaped_pin_is_rebuilt_not_reused) ... ok
test_a_reused_pin_resolves_the_pin_not_the_working_tree (tests.test_pin_honesty_and_integrity.ReusedPinResolvesTheImportToItself.test_a_reused_pin_resolves_the_pin_not_the_working_tree) ... ok
test_empty_driver_paths_still_returns_empty_string (tests.test_pin_honesty_and_integrity.UnpinnedTextIsByteIdentical.test_empty_driver_paths_still_returns_empty_string) ... ok
test_unpinned_text_is_byte_identical (tests.test_pin_honesty_and_integrity.UnpinnedTextIsByteIdentical.test_unpinned_text_is_byte_identical) ... ok

----------------------------------------------------------------------
Ran 7 tests in 1.919s

OK
```

### lint: FAIL
```
$ ruff check specfuse .specfuse/scripts tests scripts
help: Add explicit `check=False`

PLW1510 `subprocess.run` without explicit `check` argument
   --> tests/test_pin_honesty_and_integrity.py:228:20
    |
226 |                 "print(L.__file__)\n"
227 |             ) % (pin_dir,)
228 |             proc = subprocess.run(
    |                    ^^^^^^^^^^^^^^
229 |                 [sys.executable, "-c", probe_code], cwd=str(REPO_ROOT),
230 |                 env=env, capture_output=True, text=True, timeout=60,
    |
help: Add explicit `check=False`

Found 2 errors.
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml

```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 71 events.jsonl file(s), 1918 event(s) checked
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### roadmap-link-gate: PASS
```
$ python3 .specfuse/scripts/roadmap_link_gate.py
WARN: roadmap.md:29: FEAT-2026-0011's Detail cell is '—' but a detail section already exists in roadmap.md — link it, e.g. '[→ detail](#feat-2026-0011)' or '[→ archive](roadmap-archive.md#feat-2026-0011)'
roadmap link lint: checked roadmap.md + roadmap-archive.md link graph — 0 error(s), 1 warning(s)
```

### arm-sweep-gate: PASS
```
$ python3 .specfuse/scripts/arm_sweep_gate.py
branch-observation table:
  budget_projection          observed=[clean, fired]; NEVER not_evaluable
  judge_editing              observed=[clean, fired]; NEVER not_evaluable
  decision_class_paths       observed=[clean, fired]; NEVER not_evaluable
  retroactive_edits          observed=[clean, fired]; NEVER not_evaluable
  drift_caps                 observed=[clean, fired]; NEVER not_evaluable
  missing_provenance         observed=[clean, fired]; NEVER not_evaluable
  open_questions_human_only  observed=[clean, fired]; NEVER not_evaluable
  plan_next_lint             observed=[clean]; NEVER fired, NEVER not_evaluable
evaluable=32 evaluated=32 could_not_evaluate=0 excluded_no_baseline=45
ok: 32 evaluable feature(s) swept clean, no not_evaluable verdicts
NO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output — the lines above are the tail only, and may be unrelated to the failure. Run the command directly.
```

### monitoring-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_monitoring.py .specfuse/monitoring.yml.example
OK — monitoring config is structurally valid (or absent).
```

### feature_oracle: PASS
```
$ python3 -m unittest tests.test_installed_copy_driver_e2e -q
----------------------------------------------------------------------
Ran 9 tests in 4.296s

OK
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0109-tiered-verification/WU-09-pin-honesty-and-integrity.md b/.specfuse/features/FEAT-2026-0109-tiered-verification/WU-09-pin-honesty-and-integrity.md
index 9f5238d..65822f9 100644
--- a/.specfuse/features/FEAT-2026-0109-tiered-verification/WU-09-pin-honesty-and-integrity.md
+++ b/.specfuse/features/FEAT-2026-0109-tiered-verification/WU-09-pin-honesty-and-integrity.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0109/T09
 type: implementation
-status: pending
-attempts: 0
+status: in_progress
+attempts: 1
 planned_cost_usd: 4.00
 oracle_env: macos_local
 produces_driver_helper: format_driver_staleness_warning
@@ -14,6 +14,11 @@ duration_seconds: 671.496
 cost_usd: 1.207852
 input_tokens: 56
 output_tokens: 28088
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.16.0
+started_at: 2026-09-09T12:00:18.059806+00:00
 ---
 
 # A pinned run says what it actually does, and never trusts a half-reaped pin
diff --git a/specfuse/loop/build_provenance.py b/specfuse/loop/build_provenance.py
index ecfb241..57370ec 100644
--- a/specfuse/loop/build_provenance.py
+++ b/specfuse/loop/build_provenance.py
@@ -172,18 +172,49 @@ def pin_dir_for(tree_hash: str) -> Path:
     return pin_cache_root() / tree_hash
 
 
+def _pin_is_complete(repo_root: Path, pin_dir: Path) -> bool:
+    """True iff every file `materialize_pin` would copy from *repo_root* is
+    still present, at the same size, under *pin_dir* (FOLLOW-UPS.md #3271).
+
+    The marker alone answers "was this pin built from this tree hash", not
+    "does it still hold what it was built from" -- an OS tmp-reaper can
+    remove files from an on-disk pin without touching its marker, since
+    `shutil.copytree` preserves source mtimes and a freshly written pin
+    already looks old to an age-based reaper. Trusting the marker alone
+    reintroduces #1040's "confidently wrong" failure mode: a pin missing
+    files still reported as the running build.
+    """
+    src_root = repo_root / "specfuse"
+    dst_root = pin_dir / "specfuse"
+    for src_file in src_root.rglob("*"):
+        if src_file.is_dir() or src_file.suffix == ".pyc" or "__pycache__" in src_file.parts:
+            continue
+        rel = src_file.relative_to(src_root)
+        dst_file = dst_root / rel
+        try:
+            if not dst_file.is_file() or dst_file.stat().st_size != src_file.stat().st_size:
+                return False
+        except OSError:
+            return False
+    return True
+
+
 def materialize_pin(repo_root: Path, tree_hash: str) -> Path:
     """Copy *repo_root*'s `specfuse/` package to a pin keyed on *tree_hash*.
 
     Idempotent: a pin already materialized for this tree hash (the marker
-    file matches) is reused as-is, so a second process pinning the same
-    commit does not re-copy. Builds into a sibling temp directory first and
-    installs it with a single `os.replace` so a reader never observes a
-    half-copied pin.
+    file matches AND its content is still complete, per `_pin_is_complete`)
+    is reused as-is, so a second process pinning the same commit does not
+    re-copy. A pin whose marker matches but whose content has been partially
+    reaped is rebuilt, not reused (FOLLOW-UPS.md #3271). Builds into a
+    sibling temp directory first and installs it with a single `os.replace`
+    so a reader never observes a half-copied pin.
     """
     pin_dir = pin_dir_for(tree_hash)
     marker = pin_dir / _PIN_MARKER_NAME
-    if marker.is_file() and marker.read_text(encoding="utf-8").strip() == tree_hash:
+    if (marker.is_file()
+            and marker.read_text(encoding="utf-8").strip() == tree_hash
+            and _pin_is_complete(repo_root, pin_dir)):
         return pin_dir
 
     cache_root = pin_cache_root()
@@ -197,11 +228,11 @@ def materialize_pin(repo_root: Path, tree_hash: str) -> Path:
         (staging / PIN_LAUNCHER_NAME).write_text(_PIN_LAUNCHER_SOURCE, encoding="utf-8")
         (staging / _PIN_MARKER_NAME).write_text(tree_hash, encoding="utf-8")
         if pin_dir.exists():
-            # Another process won the race and finished first; its copy is
-            # equally valid (same tree hash), so keep it and discard ours.
-            shutil.rmtree(staging, ignore_errors=True)
-        else:
-            os.replace(staging, pin_dir)
+            # Either another process won the race and finished first, or
+            # this is a reaped pin we just decided to rebuild -- either way
+            # a complete fresh copy replaces whatever is standing there.
+            shutil.rmtree(pin_dir, ignore_errors=True)
+        os.replace(staging, pin_dir)
     finally:
         if staging.exists():
             shutil.rmtree(staging, ignore_errors=True)
diff --git a/specfuse/loop/loop.py b/specfuse/loop/loop.py
index c5571dc..ba1de3e 100644
--- a/specfuse/loop/loop.py
+++ b/specfuse/loop/loop.py
@@ -3075,7 +3075,10 @@ def format_deliverable_missing_note(
     return "\n".join(lines)
 
 
-def format_driver_staleness_warning(wu_id: str, driver_paths: list) -> str:
+def format_driver_staleness_warning(
+    wu_id: str, driver_paths: list,
+    pinned_tree: "str | None" = None, next_pin_tree: "str | None" = None,
+) -> str:
     """Render the driver-editing staleness warning for `wu_id`, or "" if
     `driver_paths` is empty (FEAT-2026-0075/T02).
 
@@ -3084,10 +3087,27 @@ def format_driver_staleness_warning(wu_id: str, driver_paths: list) -> str:
     process dispatches next — including a close armed to verify it. The
     message names the offending unit and every path it touched, and states
     the required remedy explicitly rather than leaving the reader to infer it.
+
+    *pinned_tree* is this process's pin (`SPECFUSE_LOOP_PINNED_TREE`), or
+    `None` when unpinned. When set, the unpinned remedy above is false: this
+    process does not need to stop, because the NEXT process re-pins from
+    `next_pin_tree` (`HEAD^{tree}` right after the squash) anyway, so it
+    keeps dispatching against its own `pinned_tree` snapshot untouched by the
+    edit (FEAT-2026-0109/T09, FOLLOW-UPS.md #3270). The unpinned branch's
+    wording is unchanged so `UnpinnedRunStillHalts` keeps passing byte-for-byte.
     """
     if not driver_paths:
         return ""
     paths = ", ".join(driver_paths)
+    if pinned_tree is not None:
+        return (
+            f"PINNED DRIVER PROCESS: {wu_id} edited the driver itself "
+            f"({paths}). This process is running from a pinned build of "
+            f"tree {pinned_tree}, so it is unaffected by that edit and "
+            f"continues dispatching against its own {pinned_tree} snapshot. "
+            f"The edit takes effect in tree {next_pin_tree}, the next "
+            f"process to pin."
+        )
     return (
         f"STALE DRIVER PROCESS: {wu_id} edited the driver itself ({paths}). "
         f"This process cached the pre-edit versions of those modules at "
@@ -3155,7 +3175,10 @@ def merge_gate_driver_edits(process_edits: list, recorded_edits: list) -> list:
     return merged
 
 
-def format_driver_staleness_summary(edits: list, dispatched_after: list) -> str:
+def format_driver_staleness_summary(
+    edits: list, dispatched_after: list,
+    pinned_tree: "str | None" = None,
+) -> str:
     """Render the gate-completion staleness summary (FEAT-2026-0075/T03).
 
     `edits` is `[(wu_id, driver_paths), ...]` for units that edited the
@@ -3168,20 +3191,38 @@ def format_driver_staleness_summary(edits: list, dispatched_after: list) -> str:
     of reconstructing the fact from `ps` output and `started_at` timestamps.
     Returns "" when `edits` is empty so a gate with no driver-editing unit
     stays silent.
+
+    *pinned_tree* is THIS process's pin (`SPECFUSE_LOOP_PINNED_TREE`), or
+    `None` when unpinned. `dispatched_after` is computed from this same
+    process's own edits, so when this process is pinned those units executed
+    the pinned snapshot unaffected by the edit, not a stale pre-edit module —
+    the unpinned tail's "fresh driver process is required" claim would be
+    false (FEAT-2026-0109/T09, FOLLOW-UPS.md #3270). Unpinned wording is
+    unchanged byte-for-byte.
     """
     if not edits:
         return ""
-    lines = ["STALE DRIVER PROCESS (gate summary):"]
+    header = ("PINNED DRIVER PROCESS (gate summary):" if pinned_tree is not None
+              else "STALE DRIVER PROCESS (gate summary):")
+    lines = [header]
     for wu_id, paths in edits:
         lines.append(f"  - {wu_id} edited the driver: {', '.join(paths)}")
     if dispatched_after:
         affected = ", ".join(dispatched_after)
-        lines.append(
-            f"  Dispatched after the edit above in this same process: "
-            f"{affected} — each executed the pre-edit module(s), not what "
-            f"the edit(s) wrote. A fresh driver process is required before "
-            f"any of these can be trusted as a verification of the change."
-        )
+        if pinned_tree is not None:
+            lines.append(
+                f"  Dispatched after the edit above in this same process: "
+                f"{affected} — this process is pinned to tree {pinned_tree}, "
+                f"unaffected by the edit(s) above; each executed that same "
+                f"pinned snapshot, not the pre-edit working-tree module(s)."
+            )
+        else:
+            lines.append(
+                f"  Dispatched after the edit above in this same process: "
+                f"{affected} — each executed the pre-edit module(s), not what "
+                f"the edit(s) wrote. A fresh driver process is required before "
+                f"any of these can be trusted as a verification of the change."
+            )
     return "\n".join(lines)
 
 
@@ -8947,8 +8988,13 @@ def run(
                         if sha is not None:
                             _changed = changed_paths_for_commit(sha, REPO_ROOT)
                             _driver_paths = driver_paths_in(_changed)
+                            _pinned_tree_now = os.environ.get(PINNED_BUILD_ENV_VAR)
+                            _next_pin_tree_now = (
+                                head_tree_hash(REPO_ROOT)
+                                if _pinned_tree_now is not None else None)
                             _warning = format_driver_staleness_warning(
-                                wu.wu_id, _driver_paths)
+                                wu.wu_id, _driver_paths,
+                                _pinned_tree_now, _next_pin_tree_now)
                             if _warning:
                                 print(_warning)
                                 # Recorded for the gate-completion summary
@@ -9731,7 +9777,8 @@ def run(
             else:
                 _dispatched_after = []
             _staleness_summary = format_driver_staleness_summary(
-                _gate_edits, _dispatched_after)
+                _gate_edits, _dispatched_after,
+                pinned_tree=os.environ.get(PINNED_BUILD_ENV_VAR))
             if _staleness_summary:
                 print(f"\n{_staleness_summary}")
                 staleness_gate_events.append(build_event(

```
