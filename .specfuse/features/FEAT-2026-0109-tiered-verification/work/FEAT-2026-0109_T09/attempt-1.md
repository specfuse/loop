### tests: PASS
```
$ python3 -m unittest tests.test_pin_honesty_and_integrity -v -b
test_a_file_deleted_behind_the_pin_is_restored_on_reuse (tests.test_pin_honesty_and_integrity.AReapedPinIsRebuiltNotReused.test_a_file_deleted_behind_the_pin_is_restored_on_reuse) ... ok
test_import_resolves_to_pin (tests.test_pin_honesty_and_integrity.AReusedPinResolvesThePinNotTheWorkingTree.test_import_resolves_to_pin) ... ok
test_gate_summary_is_pin_aware_too (tests.test_pin_honesty_and_integrity.PinnedSeamAndSummaryArePinAware.test_gate_summary_is_pin_aware_too) ... ok
test_pinned_seam_prints_pin_aware_text (tests.test_pin_honesty_and_integrity.PinnedSeamAndSummaryArePinAware.test_pinned_seam_prints_pin_aware_text) ... ok
test_empty_input_contract_unchanged (tests.test_pin_honesty_and_integrity.UnpinnedTextIsByteIdentical.test_empty_input_contract_unchanged) ... ok
test_summary_text_unchanged (tests.test_pin_honesty_and_integrity.UnpinnedTextIsByteIdentical.test_summary_text_unchanged) ... ok
test_warning_text_unchanged (tests.test_pin_honesty_and_integrity.UnpinnedTextIsByteIdentical.test_warning_text_unchanged) ... ok

----------------------------------------------------------------------
Ran 7 tests in 1.848s

OK
```

### lint: FAIL
```
$ ruff check specfuse .specfuse/scripts tests scripts
29 | from tests.test_installed_copy_driver_e2e import (
30 |     REPO_ROOT,
   |     ^^^^^^^^^
31 |     _build_scaffold,
32 |     _events,
   |
help: Remove unused import: `tests.test_installed_copy_driver_e2e.REPO_ROOT`
   |
29 | from tests.test_installed_copy_driver_e2e import (
   -     REPO_ROOT,
30 |     _build_scaffold,
   |

Found 1 error.
[*] 1 fixable with the `--fix` option.
```

### agent-policy-example-lint: PASS
```
$ python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml.example && python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml

```

### event-type-gate: PASS
```
$ python3 .specfuse/scripts/event_type_gate.py
ok: no validation errors across 71 events.jsonl file(s), 1912 event(s) checked
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
Ran 9 tests in 2.972s

OK
```

## Rejected working-tree diff (discarded by git reset on block)

```diff
diff --git a/.specfuse/features/FEAT-2026-0109-tiered-verification/WU-09-pin-honesty-and-integrity.md b/.specfuse/features/FEAT-2026-0109-tiered-verification/WU-09-pin-honesty-and-integrity.md
index 9eaa1fb..61d6c96 100644
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
@@ -10,6 +10,11 @@ produces:
   - specfuse/loop/loop.py
   - specfuse/loop/build_provenance.py
   - tests/test_pin_honesty_and_integrity.py
+model: sonnet
+effort: medium
+gate_set: code
+driver_version: 0.16.0
+started_at: 2026-09-09T11:43:42.667369+00:00
 ---
 
 # A pinned run says what it actually does, and never trusts a half-reaped pin
diff --git a/specfuse/loop/build_provenance.py b/specfuse/loop/build_provenance.py
index ecfb241..32708d5 100644
--- a/specfuse/loop/build_provenance.py
+++ b/specfuse/loop/build_provenance.py
@@ -102,6 +102,16 @@ _PIN_CACHE_ENV_VAR = "SPECFUSE_PIN_CACHE_DIR"
 #: unidentified, never trusted silently.
 _PIN_MARKER_NAME = ".specfuse-pin-tree"
 
+#: Manifest of every file the pin's `specfuse/` copy held at materialize
+#: time, written alongside the marker. The marker alone only proves a pin
+#: was *once* built for this tree hash -- an OS tmp reaper can delete files
+#: from inside it afterward without touching the marker, and a reuse check
+#: that looks only at the marker then hands back a pin missing files as if
+#: it were the complete build (FEAT-2026-0109/T09, FOLLOW-UPS.md #3271).
+#: Checking every listed path still exists is what tells "still complete"
+#: apart from "reaped since".
+_PIN_MANIFEST_NAME = ".specfuse-pin-manifest"
+
 #: The launcher `main()` re-execs through once a pin is materialized. Its own
 #: directory becomes `sys.path[0]` for a script invocation (probed fact #2 in
 #: FEAT-2026-0109/T08's work-unit body), so it lives beside the pinned
@@ -172,18 +182,52 @@ def pin_dir_for(tree_hash: str) -> Path:
     return pin_cache_root() / tree_hash
 
 
+def _manifest_lines_for(specfuse_dir: Path) -> list:
+    """Relative paths of every file under *specfuse_dir*, sorted."""
+    return sorted(
+        str(p.relative_to(specfuse_dir))
+        for p in specfuse_dir.rglob("*") if p.is_file()
+    )
+
+
+def _pin_is_complete(pin_dir: Path) -> bool:
+    """Whether every file the manifest recorded is still present.
+
+    No manifest (a pin built before this check existed) is treated as
+    incomplete rather than trusted blind -- the whole point is that the
+    marker's presence is not proof of content.
+    """
+    manifest = pin_dir / _PIN_MANIFEST_NAME
+    if not manifest.is_file():
+        return False
+    try:
+        expected = manifest.read_text(encoding="utf-8").splitlines()
+    except OSError:
+        return False
+    specfuse_dir = pin_dir / "specfuse"
+    return all((specfuse_dir / rel).is_file() for rel in expected if rel)
+
+
 def materialize_pin(repo_root: Path, tree_hash: str) -> Path:
     """Copy *repo_root*'s `specfuse/` package to a pin keyed on *tree_hash*.
 
-    Idempotent: a pin already materialized for this tree hash (the marker
-    file matches) is reused as-is, so a second process pinning the same
-    commit does not re-copy. Builds into a sibling temp directory first and
-    installs it with a single `os.replace` so a reader never observes a
-    half-copied pin.
+    Idempotent: a pin already materialized for this tree hash is reused only
+    when it is still **complete** -- the marker matching *tree_hash* AND
+    every file its manifest recorded still present. A marker match alone
+    used to be enough, but an OS tmp reaper can delete files out of a pin
+    without touching the marker, and a partially reaped pin reused as-is is
+    reported as the running build while missing modules it actually holds
+    (#1040's failure mode, reintroduced -- FEAT-2026-0109/T09). An
+    incomplete pin is rebuilt in place rather than trusted.
+
+    Builds into a sibling temp directory first and installs it with a
+    single `os.replace` so a reader never observes a half-copied pin.
     """
     pin_dir = pin_dir_for(tree_hash)
     marker = pin_dir / _PIN_MARKER_NAME
-    if marker.is_file() and marker.read_text(encoding="utf-8").strip() == tree_hash:
+    if (marker.is_file()
+            and marker.read_text(encoding="utf-8").strip() == tree_hash
+            and _pin_is_complete(pin_dir)):
         return pin_dir
 
     cache_root = pin_cache_root()
@@ -196,10 +240,20 @@ def materialize_pin(repo_root: Path, tree_hash: str) -> Path:
         )
         (staging / PIN_LAUNCHER_NAME).write_text(_PIN_LAUNCHER_SOURCE, encoding="utf-8")
         (staging / _PIN_MARKER_NAME).write_text(tree_hash, encoding="utf-8")
+        manifest_lines = _manifest_lines_for(staging / "specfuse")
+        (staging / _PIN_MANIFEST_NAME).write_text(
+            "\n".join(manifest_lines) + "\n", encoding="utf-8")
         if pin_dir.exists():
-            # Another process won the race and finished first; its copy is
-            # equally valid (same tree hash), so keep it and discard ours.
-            shutil.rmtree(staging, ignore_errors=True)
+            if _pin_is_complete(pin_dir):
+                # Another process won the race and finished first; its copy
+                # is equally valid (same tree hash) and complete, so keep it
+                # and discard ours.
+                shutil.rmtree(staging, ignore_errors=True)
+            else:
+                # What's there is a reaped remnant of an earlier
+                # materialization, not a live race winner -- replace it.
+                shutil.rmtree(pin_dir, ignore_errors=True)
+                os.replace(staging, pin_dir)
         else:
             os.replace(staging, pin_dir)
     finally:
diff --git a/specfuse/loop/loop.py b/specfuse/loop/loop.py
index c5571dc..e3e039b 100644
--- a/specfuse/loop/loop.py
+++ b/specfuse/loop/loop.py
@@ -3099,6 +3099,63 @@ def format_driver_staleness_warning(wu_id: str, driver_paths: list) -> str:
     )
 
 
+def format_pinned_driver_staleness_notice(
+    wu_id: str, driver_paths: list, pinned_tree: str, next_pin_tree: "str | None",
+) -> str:
+    """Render the pin-aware counterpart to `format_driver_staleness_warning`
+    for the seam where a pinned run declines to halt (FEAT-2026-0109/T09).
+
+    Before this, the unpinned text printed here unchanged, telling the
+    operator "a fresh driver process is required before any of these can be
+    trusted" while the process did the opposite: it kept dispatching, on
+    purpose, against its own pinned snapshot. `GATE-03.md` requires the cost
+    be stated in words at the point it is incurred, not the words for a path
+    not taken. This names the pin's tree (`pinned_tree`), the tree the edit
+    takes effect in (`next_pin_tree` -- the same value the
+    `driver_staleness_detected` event records), and says plainly that this
+    process continues against its own snapshot rather than the edit just
+    written.
+    """
+    if not driver_paths:
+        return ""
+    paths = ", ".join(driver_paths)
+    next_tree = next_pin_tree or "(unresolved)"
+    return (
+        f"PINNED DRIVER PROCESS: {wu_id} edited the driver itself ({paths}), "
+        f"while this process runs pinned to build {pinned_tree}. The edit "
+        f"takes effect in tree {next_tree} -- the next driver process to "
+        f"start will pin to that tree and execute it. This process is not "
+        f"stale: it continues dispatching every remaining work unit against "
+        f"its own pinned snapshot ({pinned_tree}), not against {wu_id}'s "
+        f"edit, and that is by design."
+    )
+
+
+def format_pinned_driver_staleness_summary(edits: list, pinned_tree: str) -> str:
+    """Pin-aware counterpart to `format_driver_staleness_summary` for the
+    gate-completion summary (FEAT-2026-0109/T09) -- same follow-up as
+    `format_pinned_driver_staleness_notice`: the unpinned summary text
+    claimed a build could not be trusted when this process's pin is exactly
+    what makes it trustworthy. Returns "" when `edits` is empty, matching
+    the unpinned formatter's empty-input contract.
+    """
+    if not edits:
+        return ""
+    lines = [
+        f"PINNED DRIVER PROCESS (gate summary) -- this gate ran pinned to "
+        f"build {pinned_tree}:"
+    ]
+    for wu_id, paths in edits:
+        lines.append(f"  - {wu_id} edited the driver: {', '.join(paths)}")
+    lines.append(
+        f"  Every unit above dispatched against the pinned snapshot "
+        f"({pinned_tree}), not against these edits -- each edit takes effect "
+        f"only in the next driver process, which pins fresh from the tree "
+        f"after them."
+    )
+    return "\n".join(lines)
+
+
 def gate_driver_edits_from_events(feature_dir: Path, gate_number: int) -> list:
     """Driver edits recorded for *gate_number* by earlier driver processes (#1039).
 
@@ -8947,10 +9004,22 @@ def run(
                         if sha is not None:
                             _changed = changed_paths_for_commit(sha, REPO_ROOT)
                             _driver_paths = driver_paths_in(_changed)
-                            _warning = format_driver_staleness_warning(
-                                wu.wu_id, _driver_paths)
-                            if _warning:
-                                print(_warning)
+                            if _driver_paths:
+                                _pinned_tree = os.environ.get(PINNED_BUILD_ENV_VAR)
+                                if _pinned_tree:
+                                    # FEAT-2026-0109/T09: this process is a
+                                    # recorded pin, so the unpinned warning's
+                                    # "a fresh process is required" is false
+                                    # here — print the pin-aware counterpart
+                                    # instead, naming the pin this process
+                                    # runs on and the tree the edit takes
+                                    # effect in.
+                                    print(format_pinned_driver_staleness_notice(
+                                        wu.wu_id, _driver_paths, _pinned_tree,
+                                        head_tree_hash(REPO_ROOT)))
+                                else:
+                                    print(format_driver_staleness_warning(
+                                        wu.wu_id, _driver_paths))
                                 # Recorded for the gate-completion summary
                                 # (FEAT-2026-0075/T03) — the immediate print
                                 # above and this recording are independent;
@@ -9730,8 +9799,17 @@ def run(
                 _dispatched_after = dispatch_order[_first_edit_idx + 1:]
             else:
                 _dispatched_after = []
-            _staleness_summary = format_driver_staleness_summary(
-                _gate_edits, _dispatched_after)
+            _pinned_tree_for_summary = os.environ.get(PINNED_BUILD_ENV_VAR)
+            if _pinned_tree_for_summary:
+                # FEAT-2026-0109/T09: same distinction as the per-unit
+                # notice above — a gate that completed in a pinned process
+                # ran every edit above against its own snapshot, not the
+                # "cannot be trusted" claim the unpinned summary makes.
+                _staleness_summary = format_pinned_driver_staleness_summary(
+                    _gate_edits, _pinned_tree_for_summary)
+            else:
+                _staleness_summary = format_driver_staleness_summary(
+                    _gate_edits, _dispatched_after)
             if _staleness_summary:
                 print(f"\n{_staleness_summary}")
                 staleness_gate_events.append(build_event(

```
