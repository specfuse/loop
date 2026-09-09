#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Gate 3's two `not_met` follow-ups (FEAT-2026-0109/T09), closing both
entries `FOLLOW-UPS.md` filed against G3-CLOSE:

1. The pinned-driver seam and the gate-completion summary must say a pinned
   run is pinned and continuing, not print the pre-T08 "stop and restart"
   text while actually continuing to dispatch. Read on the subprocess's
   **stdout** — the gate oracle (`test_installed_copy_driver_e2e.py`) is
   bound to `events.jsonl` and the exit code and cannot see this surface.
2. `materialize_pin` must validate a pin's content, not only its marker,
   before reusing it — a pin partially reaped by an age-based tmp cleaner
   must be rebuilt, not reported as the running build.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT))

from tests import test_installed_copy_driver_e2e as _pinned_e2e  # noqa: E402


class PinnedSeamTextIsPinAware(unittest.TestCase):
    """Drives the same pinned-driver scenario T08's gate oracle uses
    (`PinnedRunRecordsAndSurvivesDriverEdits`) and reads the subprocess's
    stdout — the surface `FOLLOW-UPS.md` names as unread by any test bound
    to the gate's own oracle contract.
    """

    @classmethod
    def setUpClass(cls):
        cls.case = _pinned_e2e.PinnedRunRecordsAndSurvivesDriverEdits
        cls.case.setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.case.tearDownClass()

    def _pinned_tree(self):
        pinned = [e for e in self.case.events
                  if e.get("event_type") == "driver_build_pinned"]
        self.assertEqual(len(pinned), 1, self.case.events)
        return pinned[0]["payload"]["tree"]

    def _next_pin_tree(self):
        recorded = [
            e for e in self.case.events
            if e.get("event_type") == "driver_staleness_detected"
            and e.get("payload", {}).get("halted") is False
        ]
        self.assertEqual(len(recorded), 1, self.case.events)
        return recorded[0]["payload"]["next_pin_tree"]

    def test_pinned_seam_prints_pin_aware_text(self):
        stdout = self.case.proc.stdout
        pinned_tree = self._pinned_tree()
        next_pin_tree = self._next_pin_tree()

        self.assertIn(pinned_tree, stdout)
        self.assertIn(next_pin_tree, stdout)
        self.assertIn(
            "continues dispatching against its own pinned snapshot", stdout)
        # The pre-T09 wording, which told the operator to stop and restart
        # while the process kept dispatching, must not appear anywhere.
        self.assertNotIn("STALE DRIVER PROCESS:", stdout)
        self.assertNotIn(
            "stop this driver now and start a new one", stdout)

    def test_gate_summary_is_pin_aware_too(self):
        stdout = self.case.proc.stdout
        pinned_tree = self._pinned_tree()
        next_pin_tree = self._next_pin_tree()

        self.assertIn(
            f"DRIVER EDITS RECORDED (gate summary, pinned build "
            f"{pinned_tree}):", stdout)
        self.assertIn(next_pin_tree, stdout)
        self.assertIn("No restart was required.", stdout)
        self.assertNotIn("STALE DRIVER PROCESS (gate summary):", stdout)
        self.assertNotIn(
            "A fresh driver process is required before any of these can be "
            "trusted as a verification of the change.", stdout)


class UnpinnedTextIsByteIdentical(unittest.TestCase):
    """`format_driver_staleness_warning` / `format_driver_staleness_summary`
    called with no pin info must reproduce HEAD's wording byte-for-byte —
    the unpinned path is untouched by this unit."""

    def test_unpinned_text_is_byte_identical(self):
        from specfuse.loop.loop import (
            format_driver_staleness_summary, format_driver_staleness_warning)

        wu_id = "FEAT-2026-9999/T01"
        paths = ["specfuse/loop/loop.py"]
        warning = format_driver_staleness_warning(wu_id, paths)
        self.assertEqual(
            warning,
            "STALE DRIVER PROCESS: FEAT-2026-9999/T01 edited the driver "
            "itself (specfuse/loop/loop.py). This process cached the "
            "pre-edit versions of those modules at import time, so every "
            "work unit dispatched next in this process — including any "
            "close — will execute the OLD code, not what "
            "FEAT-2026-9999/T01 just wrote. A fresh driver process is "
            "required before any close can verify this change: stop this "
            "driver now and start a new one before dispatching the next "
            "work unit."
        )

        summary = format_driver_staleness_summary(
            [(wu_id, paths)], ["FEAT-2026-9999/T02"])
        self.assertEqual(
            summary,
            "STALE DRIVER PROCESS (gate summary):\n"
            "  - FEAT-2026-9999/T01 edited the driver: "
            "specfuse/loop/loop.py\n"
            "  Dispatched after the edit above in this same process: "
            "FEAT-2026-9999/T02 — each executed the pre-edit module(s), "
            "not what the edit(s) wrote. A fresh driver process is "
            "required before any of these can be trusted as a "
            "verification of the change."
        )

        # Empty-input contract, and no-`dispatched_after` shape: unchanged.
        self.assertEqual(format_driver_staleness_warning(wu_id, []), "")
        self.assertEqual(
            format_driver_staleness_summary([(wu_id, paths)], []),
            "STALE DRIVER PROCESS (gate summary):\n"
            "  - FEAT-2026-9999/T01 edited the driver: "
            "specfuse/loop/loop.py",
        )
        self.assertEqual(format_driver_staleness_summary([], []), "")


class _PinCacheEnvGuard:
    """Temporarily point the pin cache at a scratch directory (T08's
    `SPECFUSE_PIN_CACHE_DIR` override) so this suite never touches or
    reuses this repo's own real pin cache."""

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="specfuse-pin-integrity-")
        self.prev = os.environ.get("SPECFUSE_PIN_CACHE_DIR")
        os.environ["SPECFUSE_PIN_CACHE_DIR"] = str(Path(self.tmp) / "pins")
        return Path(os.environ["SPECFUSE_PIN_CACHE_DIR"])

    def __exit__(self, *exc):
        if self.prev is None:
            os.environ.pop("SPECFUSE_PIN_CACHE_DIR", None)
        else:
            os.environ["SPECFUSE_PIN_CACHE_DIR"] = self.prev
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)


class AReapedPinIsRebuiltNotReused(unittest.TestCase):

    def test_a_reaped_pin_is_rebuilt_not_reused(self):
        from specfuse.loop import build_provenance

        with _PinCacheEnvGuard():
            tree_hash = build_provenance.head_tree_hash(REPO_ROOT)
            self.assertIsNotNone(tree_hash)

            pin_dir = build_provenance.materialize_pin(REPO_ROOT, tree_hash)
            before_files = sorted(
                str(p.relative_to(pin_dir / "specfuse"))
                for p in (pin_dir / "specfuse").rglob("*") if p.is_file())
            self.assertGreater(len(before_files), 0)

            victim = pin_dir / "specfuse" / "loop" / "__init__.py"
            self.assertTrue(victim.is_file())
            victim.unlink()
            self.assertFalse(victim.is_file())

            pin_dir_again = build_provenance.materialize_pin(
                REPO_ROOT, tree_hash)
            after_files = sorted(
                str(p.relative_to(pin_dir_again / "specfuse"))
                for p in (pin_dir_again / "specfuse").rglob("*")
                if p.is_file())

            self.assertEqual(after_files, before_files)
            self.assertTrue(
                (pin_dir_again / "specfuse" / "loop" / "__init__.py")
                .is_file())


class AReusedPinResolvesThePinNotTheWorkingTree(unittest.TestCase):

    def test_a_reused_pin_resolves_the_pin_not_the_working_tree(self):
        from specfuse.loop import build_provenance

        with _PinCacheEnvGuard():
            tree_hash = build_provenance.head_tree_hash(REPO_ROOT)
            self.assertIsNotNone(tree_hash)
            pin_dir = build_provenance.materialize_pin(REPO_ROOT, tree_hash)
            # Reuse path: a second call with nothing removed must hit the
            # early "already complete" return and resolve identically.
            pin_dir_reused = build_provenance.materialize_pin(
                REPO_ROOT, tree_hash)
            self.assertEqual(pin_dir, pin_dir_reused)

            # `_run_pinned.py` re-enters `main()`; probe the resolution
            # directly instead, via the same sys.path shape the launcher
            # sets up, run out-of-process so this test process's own
            # cached `sys.modules["specfuse.loop.loop"]` can't mask a
            # working-tree fallback.
            probe = (
                "import sys\n"
                f"sys.path.insert(0, {str(pin_dir_reused)!r})\n"
                "import specfuse.loop.loop as L\n"
                "print(L.__file__)\n"
            )
            proc = subprocess.run(
                [sys.executable, "-c", probe],
                cwd=str(REPO_ROOT), capture_output=True, text=True,
                timeout=30, check=False,
            )
            self.assertEqual(
                proc.returncode, 0,
                f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
            resolved = Path(proc.stdout.strip()).resolve()
            self.assertTrue(
                str(resolved).startswith(str(pin_dir_reused.resolve())),
                f"resolved {resolved} from outside the pin "
                f"{pin_dir_reused} — the working tree at {REPO_ROOT} "
                f"leaked through instead")
            self.assertNotEqual(
                resolved, (REPO_ROOT / "specfuse" / "loop" / "loop.py")
                .resolve())


if __name__ == "__main__":
    unittest.main()
