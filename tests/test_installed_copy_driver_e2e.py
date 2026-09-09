#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The driver runs from a pinned build (FEAT-2026-0109/T08) — this gate's
`feature_oracle`.

Every other e2e suite in this repo imports `specfuse.loop.loop` (or the
scaffold's shim over it) into the test process and drives `loop.run()`
directly, with dispatch/gate-runner functions monkeypatched. That is
deliberately NOT what this file does: T08's whole subject is what happens
across a real process boundary — a fresh interpreter finding, copying, and
re-executing from a build outside the working tree — and monkeypatching a
function inside the test process can't observe any of that. So this suite
launches the driver as a genuine subprocess, over a temporary scaffold repo
that carries its own `specfuse/loop/` source tree (so the pinning path in
`_reexec_pinned` actually engages), with a stub `claude` script on `PATH`
standing in for the real CLI. It asserts only on the subprocess's exit code
and the `events.jsonl` it wrote — never on anything read back through an
import of the driver into this process.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Timeout for the whole driver subprocess — generous vs. the trivial "true"
#: gate commands and stub claude script this suite uses, matching
#: GATE_TIMEOUT_SECONDS's "generous vs. real suites" posture in loop.py.
_SUBPROCESS_TIMEOUT = 60

_CLAUDE_STUB = '''#!/usr/bin/env python3
"""Stand-in for the real `claude` CLI (FEAT-2026-0109/T08 fixture).

Reads the prompt on stdin, writes the file(s) a `PRODUCE_FILE:` directive in
the work unit's own body names (a real agent session would have written
them for real), then emits a well-formed RESULT block so verify() and the
squash path see a normal attempt.
"""
import re
import sys
from pathlib import Path

prompt = sys.stdin.read()
for match in re.finditer(r"^PRODUCE_FILE:\\s*(\\S+)\\s*$", prompt, re.MULTILINE):
    path = Path(match.group(1))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\\n# stub-claude edit\\n")
    else:
        path.write_text("# stub-claude deliverable\\n", encoding="utf-8")

print("```result")
print("status: complete")
print("summary: stub claude session")
print("```")
'''

_WU_BODY = (
    "\n\n**Context.** fixture.\n\n**Acceptance criteria.** fixture.\n\n"
    "**Do not touch.** fixture.\n\n**Verification.** fixture.\n\n"
    "**Escalation triggers.** fixture.\n\nPRODUCE_FILE: {produces}\n"
)


def _run_git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True,
                    capture_output=True, text=True)


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    _run_git(root, "config", "user.email", "test@example.com")
    _run_git(root, "config", "user.name", "Test")
    _run_git(root, "config", "gc.auto", "0")
    _run_git(root, "config", "commit.gpgSign", "false")


def _write_verification_yml(root: Path) -> None:
    (root / ".specfuse" / "verification.yml").write_text(
        "cost_tracking: false\n"
        "code:\n"
        "  - name: noop\n"
        "    command: \"true\"\n"
        "doc:\n"
        "  - name: noop\n"
        "    command: \"true\"\n"
        "plannext:\n"
        "  - name: noop\n"
        "    command: \"true\"\n"
    )


def _write_wu(fdir: Path, wu_id: str, deps: str, produces: str) -> None:
    tnn = wu_id.split("/")[-1]
    (fdir / f"WU-{tnn}.md").write_text(
        f"---\nid: {wu_id}\ntype: implementation\n"
        f"model: claude-haiku-4-5-20251001\neffort: medium\n"
        f"status: pending\nattempts: 0\nmax_attempts: 1\n"
        f"produces:\n  - {produces}\n---\n\n# {tnn}"
        + _WU_BODY.format(produces=produces)
    )


def _write_feature(root: Path, feature_id: str, slug: str,
                    wu_specs: list) -> Path:
    """wu_specs: [(wu_id, deps_list_of_ids, produces_path), ...]"""
    fdir = root / ".specfuse" / "features" / f"{feature_id}-{slug}"
    fdir.mkdir(parents=True)

    rows = []
    for wu_id, deps, produces in wu_specs:
        tnn = wu_id.split("/")[-1]
        deps_str = "[]" if not deps else f"[{', '.join(deps)}]"
        rows.append(
            f"      - id: {wu_id}\n        file: WU-{tnn}.md\n"
            f"        depends_on: {deps_str}"
        )
        _write_wu(fdir, wu_id, deps_str, produces)

    (fdir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\ntitle: Installed copy driver fixture\n"
        f"slug: {slug}\nbranch: feat/{slug}\n"
        f"roadmap_goal: exercise the pinned-build driver\nstatus: active\n"
        f"---\n\n# Plan: {slug}\n\n```yaml\ngates:\n"
        f"  - gate: 1\n    file: GATE-01.md\n    work_units:\n"
        + "\n".join(rows) + "\n```\n"
    )
    (fdir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
    return fdir


def _build_scaffold(root: Path, wu_specs: list, feature_id: str, slug: str,
                     *, with_driver_source: bool) -> None:
    _init_repo(root)
    (root / ".specfuse" / "features").mkdir(parents=True)
    _write_verification_yml(root)
    if with_driver_source:
        shutil.copytree(
            REPO_ROOT / "specfuse", root / "specfuse",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    _write_feature(root, feature_id, slug, wu_specs)
    (root / ".gitignore").write_text(
        ".specfuse/.loop.lock\n.specfuse/.scratch-*\n"
        ".specfuse/scripts/__pycache__/\nspecfuse/**/__pycache__/\n"
    )
    _run_git(root, "add", ".")
    _run_git(root, "commit", "-q", "-m", "scaffold fixture")


def _stub_claude_bin() -> Path:
    bindir = Path(tempfile.mkdtemp(prefix="specfuse-claude-stub-"))
    stub = bindir / "claude"
    stub.write_text(_CLAUDE_STUB, encoding="utf-8")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return bindir


def _run_driver(root: Path, feature_id: str, *, bindir: Path,
                 pin_cache_dir: Path, extra_pythonpath: "str | None" = None,
                 extra_args: "list | None" = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
    env["SPECFUSE_PIN_CACHE_DIR"] = str(pin_cache_dir)
    if extra_pythonpath:
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            extra_pythonpath if not existing
            else f"{extra_pythonpath}{os.pathsep}{existing}")
    args = [sys.executable, "-m", "specfuse.loop.loop",
            "--feature", feature_id, "--no-autosync", *(extra_args or [])]
    return subprocess.run(
        args, cwd=str(root), env=env, capture_output=True, text=True,
        timeout=_SUBPROCESS_TIMEOUT, check=False,
    )


def _events(root: Path, feature_dir_name: str) -> list:
    events_path = root / ".specfuse" / "features" / feature_dir_name / "events.jsonl"
    if not events_path.is_file():
        return []
    out = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


class PinnedRunRecordsAndSurvivesDriverEdits(unittest.TestCase):
    """One real subprocess run of a two-implementation-unit gate, where the
    first unit's squash really touches `specfuse/loop/loop.py`. Every
    assertion below reads that single run's exit code and events.jsonl."""

    FEATURE_ID = "FEAT-2026-8801"
    SLUG = "pinned-driver-edit"

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="specfuse-pinned-run-")
        cls.root = Path(cls._tmp) / "repo"
        cls.pin_cache_dir = Path(cls._tmp) / "pins"
        cls.bindir = _stub_claude_bin()
        _build_scaffold(
            cls.root,
            wu_specs=[
                (f"{cls.FEATURE_ID}/T01", [], "specfuse/loop/loop.py"),
                (f"{cls.FEATURE_ID}/T02", [f"{cls.FEATURE_ID}/T01"], "notes.txt"),
            ],
            feature_id=cls.FEATURE_ID, slug=cls.SLUG, with_driver_source=True,
        )
        cls.proc = _run_driver(
            cls.root, cls.FEATURE_ID, bindir=cls.bindir,
            pin_cache_dir=cls.pin_cache_dir,
        )
        cls.events = _events(cls.root, f"{cls.FEATURE_ID}-{cls.SLUG}")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)
        shutil.rmtree(cls.bindir, ignore_errors=True)

    def test_process_exit_code_is_clean(self):
        self.assertEqual(
            self.proc.returncode, 0,
            f"stdout:\n{self.proc.stdout}\nstderr:\n{self.proc.stderr}")

    def test_the_run_records_the_build_it_executed(self):
        pinned = [e for e in self.events if e.get("event_type") == "driver_build_pinned"]
        self.assertEqual(len(pinned), 1, self.events)
        payload = pinned[0]["payload"]
        self.assertTrue(payload.get("tree"))
        recorded_path = Path(payload["path"]).resolve()
        self.assertTrue(
            str(recorded_path).startswith(str(self.pin_cache_dir.resolve())),
            f"recorded path {recorded_path} is not under the pin cache "
            f"{self.pin_cache_dir} — it must be the pin, not the working "
            f"tree's specfuse/loop/")
        self.assertNotEqual(recorded_path, (self.root / "specfuse" / "loop").resolve())

    def test_a_driver_edit_does_not_halt_the_run(self):
        halting = [
            e for e in self.events
            if e.get("event_type") == "driver_staleness_detected"
            and e.get("payload", {}).get("halted") is True
        ]
        self.assertEqual(halting, [])
        self.assertNotEqual(self.proc.returncode, 3)

    def test_the_driver_edit_is_still_recorded(self):
        recorded = [
            e for e in self.events
            if e.get("event_type") == "driver_staleness_detected"
            and e.get("payload", {}).get("halted") is False
        ]
        self.assertEqual(len(recorded), 1, self.events)
        payload = recorded[0]["payload"]
        self.assertEqual(payload.get("wu_id"), f"{self.FEATURE_ID}/T01")
        self.assertIn("specfuse/loop/loop.py", payload.get("driver_paths", []))
        self.assertTrue(payload.get("next_pin_tree"))

    def test_a_moving_working_tree_does_not_move_the_running_build(self):
        pinned = [e for e in self.events if e.get("event_type") == "driver_build_pinned"][0]
        recorded_edit = [
            e for e in self.events
            if e.get("event_type") == "driver_staleness_detected"
            and e.get("payload", {}).get("halted") is False
        ][0]
        pinned_tree = pinned["payload"]["tree"]
        next_tree = recorded_edit["payload"]["next_pin_tree"]
        self.assertNotEqual(
            pinned_tree, next_tree,
            "the driver edit's squash changed HEAD^{tree}; the running "
            "pin must still report the ORIGINAL tree it was built from, "
            "distinct from the tree the edit takes effect in")
        # And T02 (dispatched after the edit, in the same process) still
        # completed — the pinned process's own behaviour was unaffected.
        self.assertTrue((self.root / "notes.txt").is_file())


class UnpinnedRunStillHalts(unittest.TestCase):
    """Pinning declined (an unwritable pin cache) — the driver-restart halt
    must be byte-identical to the pre-T08 behaviour."""

    FEATURE_ID = "FEAT-2026-8802"
    SLUG = "unpinned-still-halts"

    def test_halt_event_and_exit_code_are_unchanged(self):
        with tempfile.TemporaryDirectory(prefix="specfuse-unpinned-") as tmp:
            root = Path(tmp) / "repo"
            # A regular file where the pin cache root would go: materialize_pin's
            # mkdir(parents=True) raises OSError, so _reexec_pinned declines and
            # this process runs unpinned throughout.
            blocked_cache = Path(tmp) / "blocked-cache"
            blocked_cache.write_text("not a directory\n")
            bindir = _stub_claude_bin()
            try:
                _build_scaffold(
                    root,
                    wu_specs=[
                        (f"{self.FEATURE_ID}/T01", [], "specfuse/loop/loop.py"),
                        (f"{self.FEATURE_ID}/T02", [f"{self.FEATURE_ID}/T01"], "notes.txt"),
                    ],
                    feature_id=self.FEATURE_ID, slug=self.SLUG,
                    with_driver_source=True,
                )
                proc = _run_driver(
                    root, self.FEATURE_ID, bindir=bindir,
                    pin_cache_dir=blocked_cache,
                )
                events = _events(root, f"{self.FEATURE_ID}-{self.SLUG}")
            finally:
                shutil.rmtree(bindir, ignore_errors=True)

        self.assertEqual(
            proc.returncode, 3,
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
        halting = [
            e for e in events
            if e.get("event_type") == "driver_staleness_detected"
            and e.get("payload", {}).get("halted") is True
        ]
        self.assertEqual(len(halting), 1, events)
        payload = halting[0]["payload"]
        for key in ("wu_id", "driver_paths", "remaining_wu_ids",
                    "resume_command", "reason"):
            self.assertIn(key, payload)
        self.assertEqual(
            [e for e in events if e.get("event_type") == "driver_build_pinned"], [])


class ProjectWithoutDriverSourceIsUnaffected(unittest.TestCase):
    """A downstream project's working tree has no `specfuse/loop/` of its
    own — no pin, no re-entry, no new event, no behaviour change."""

    FEATURE_ID = "FEAT-2026-8803"
    SLUG = "no-driver-source"

    def test_no_pin_materialized_no_new_event(self):
        with tempfile.TemporaryDirectory(prefix="specfuse-nosource-") as tmp:
            root = Path(tmp) / "repo"
            pin_cache_dir = Path(tmp) / "pins"
            bindir = _stub_claude_bin()
            try:
                _build_scaffold(
                    root,
                    wu_specs=[(f"{self.FEATURE_ID}/T01", [], "notes.txt")],
                    feature_id=self.FEATURE_ID, slug=self.SLUG,
                    with_driver_source=False,
                )
                proc = _run_driver(
                    root, self.FEATURE_ID, bindir=bindir,
                    pin_cache_dir=pin_cache_dir,
                    extra_pythonpath=str(REPO_ROOT),
                )
                events = _events(root, f"{self.FEATURE_ID}-{self.SLUG}")
            finally:
                shutil.rmtree(bindir, ignore_errors=True)

        self.assertEqual(
            proc.returncode, 0,
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
        self.assertEqual(
            [e for e in events if e.get("event_type") == "driver_build_pinned"], [])
        self.assertEqual(
            [e for e in events if e.get("event_type") == "driver_staleness_detected"], [])
        self.assertFalse(
            pin_cache_dir.is_dir() and any(pin_cache_dir.iterdir()),
            "no driver source tree means nothing should ever be written "
            "under the pin cache")


class BuildProvenanceThreeStates(unittest.TestCase):
    """`out_of_tree_warning`'s three states (FEAT-2026-0109/T08). This is a
    direct in-process import of `build_provenance` — NOT `loop.py` — so it
    stays inside this file's grep constraint while covering the module the
    work unit is extending.

    In-tree (`None`) and unidentified-out-of-tree (verbatim "confidently
    wrong" text) are already covered end to end by `test_build_provenance.py`
    and untouched by this unit; only the third state — a recorded pin — is
    new, so only it is tested here.
    """

    def test_a_recorded_pin_reports_both_hashes_without_the_alarming_text(self):
        from specfuse.loop import build_provenance

        with tempfile.TemporaryDirectory(prefix="specfuse-pin-state-") as tmp:
            root = Path(tmp) / "checkout"
            (root / "specfuse" / "loop").mkdir(parents=True)
            (root / "specfuse" / "loop" / "loop.py").write_text("# checkout\n")
            subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email",
                            "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name",
                            "Test"], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "c1"],
                           check=True)
            working_tree_hash = build_provenance.head_tree_hash(root)
            self.assertIsNotNone(working_tree_hash)

            pin_root = Path(tmp) / "pins" / "deadbeef0123"
            (pin_root / "specfuse" / "loop").mkdir(parents=True)
            (pin_root / build_provenance._PIN_MARKER_NAME).write_text(
                pin_root.name, encoding="utf-8")
            running = pin_root / "specfuse" / "loop"

            orig = build_provenance.running_package_dir
            build_provenance.running_package_dir = lambda: running
            try:
                message = build_provenance.out_of_tree_warning(root)
            finally:
                build_provenance.running_package_dir = orig

            self.assertIsNotNone(message)
            self.assertNotIn("confidently wrong", message)
            self.assertIn(pin_root.name, message)          # the pinned tree
            self.assertIn(working_tree_hash, message)       # the working tree, now

    def test_pinned_build_info_rejects_an_unmatched_marker(self):
        """A directory under the cache root without a matching marker is
        still unidentified — sitting under the cache path is not a free
        pass, only a marker whose content matches its own directory counts."""
        from specfuse.loop import build_provenance

        with tempfile.TemporaryDirectory(prefix="specfuse-pin-state-") as tmp:
            pin_root = Path(tmp) / "some-dir"
            (pin_root / "specfuse" / "loop").mkdir(parents=True)
            (pin_root / build_provenance._PIN_MARKER_NAME).write_text(
                "not-the-directory-name", encoding="utf-8")

            self.assertIsNone(
                build_provenance.pinned_build_info(pin_root / "specfuse" / "loop"))


if __name__ == "__main__":
    unittest.main()
