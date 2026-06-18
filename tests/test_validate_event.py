#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Tests for .specfuse/scripts/validate-event.py.

Coverage strategy: in-process tests (importlib) exercise every function branch
directly so that `coverage run --source=.specfuse/scripts` sees all paths.
Subprocess tests (TestValidateEventSubprocess) preserve the end-to-end
exit-code contract per LEARNINGS [FEAT-2026-0003/G2-LESSONS].

Two-case rule (LEARNINGS [FEAT-2026-0003/G2-LESSONS]): every "rejects
malformed input" class is paired with a "accepts valid input" class.
Regression case (LEARNINGS [FEAT-2026-0005/G1-LESSONS]): TestValidateEventValid
includes a test whose envelope mirrors a real FEAT-2026-0008 event.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".specfuse/scripts/validate-event.py"
FEAT_0008_EVENTS = (
    REPO_ROOT
    / ".specfuse/features/FEAT-2026-0008-driver-completeness-guard/events.jsonl"
)

# ── Bundled schemas ────────────────────────────────────────────────────────────
# Mirrors orchestrator/shared/schemas/event.schema.json; source pattern and
# event_type enum are intentionally identical to pin the documented contract.

_ENVELOPE_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "timestamp", "correlation_id", "event_type",
        "source", "source_version", "payload",
    ],
    "properties": {
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "pattern": (
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
            ),
        },
        "correlation_id": {
            "type": "string",
            "pattern": r"^FEAT-\d{4}-\d{4}(/T\d{2})?$",
        },
        "event_type": {
            "type": "string",
            "enum": [
                "feature_created", "spec_validated", "task_graph_drafted",
                "template_coverage_checked", "plan_ready", "plan_generated",
                "plan_approved", "task_created", "task_ready", "task_started",
                "task_completed", "task_blocked", "spec_issue_raised",
                "override_applied", "override_expired", "human_escalation",
                "feature_state_changed", "test_plan_authored",
                "qa_execution_completed", "qa_execution_failed",
                "qa_regression_filed", "qa_regression_resolved",
                "escalation_resolved", "regression_suite_curated",
                "spec_issue_resolved", "spec_issue_routed",
            ],
        },
        "source": {
            "type": "string",
            # Matches the real schema; "driver" is intentionally absent.
            "pattern": (
                r"^(human|specs|pm|qa|config-steward|merge-watcher"
                r"|component:[a-z0-9][a-z0-9-]*)$"
            ),
        },
        "source_version": {"type": "string", "minLength": 1},
        "payload": {"type": "object"},
    },
}

# Per-type schema for task_started — used to exercise the per-type branch.
_TASK_STARTED_PAYLOAD_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["issue_url", "branch"],
    "properties": {
        "issue_url": {
            "type": "string",
            "pattern": r"^https://github\.com/[^/]+/[^/]+/issues/\d+$",
        },
        "branch": {"type": ["string", "null"]},
    },
}


def _populate_schema_dir(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "event.schema.json").write_text(
        json.dumps(_ENVELOPE_SCHEMA), encoding="utf-8"
    )
    events_dir = root / "events"
    events_dir.mkdir(exist_ok=True)
    (events_dir / "task_started.schema.json").write_text(
        json.dumps(_TASK_STARTED_PAYLOAD_SCHEMA), encoding="utf-8"
    )


# ── Module-level setup ─────────────────────────────────────────────────────────
# Create a self-contained temp schema root, set env, then load the module once.
# This keeps tests CI-portable (no orchestrator sibling repo required).

_SCHEMA_TMPDIR_OBJ = tempfile.TemporaryDirectory()
_SCHEMA_ROOT = Path(_SCHEMA_TMPDIR_OBJ.name)
_populate_schema_dir(_SCHEMA_ROOT)

# Set the schema-root env BEFORE importing the package: validate_event resolves
# SCHEMA_ROOT into a module-level constant at import time.
os.environ["SPECFUSE_SCHEMA_ROOT"] = str(_SCHEMA_ROOT)

# The driver code lives in the specfuse.loop package now (FEAT-2026-0019); the
# .specfuse/scripts/validate-event.py shim re-exports it. Import the package
# directly so in-process mock.patch.object(ve, ...) patches the same module the
# functions read their globals from. `SCRIPT` (above) is still used by the
# subprocess tests, which exercise the shim end-to-end. If the package was already
# imported by an earlier test (stale SCHEMA_ROOT), reload it now that the env is set.
import importlib as _importlib  # noqa: E402
import specfuse.loop.validate_event as _ve_mod  # noqa: E402
_ve_mod = _importlib.reload(_ve_mod)

ve = _ve_mod  # brevity alias


# ── Helpers ────────────────────────────────────────────────────────────────────

def _valid_event(**overrides: object) -> dict:
    base: dict = {
        "timestamp": "2026-04-20T14:32:05Z",
        "correlation_id": "FEAT-2026-0001",
        "event_type": "task_completed",
        "source": "human",
        "source_version": "n/a",
        "payload": {},
    }
    base.update(overrides)
    return base


def _valid_json(**overrides: object) -> str:
    return json.dumps(_valid_event(**overrides))


def _call_main(argv: list[str], stdin_data: str = "") -> tuple[int, str, str]:
    """Invoke ve.main() in-process; return (returncode, stdout, stderr)."""
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with (
        mock.patch.object(sys, "argv", [str(SCRIPT)] + argv),
        mock.patch("sys.stdin", io.StringIO(stdin_data)),
        mock.patch("sys.stdout", out_buf),
        mock.patch("sys.stderr", err_buf),
    ):
        try:
            rc = ve.main()
        except SystemExit as exc:
            rc = exc.code
    return rc, out_buf.getvalue(), err_buf.getvalue()


# ── Test classes ───────────────────────────────────────────────────────────────


class TestValidateEventValid(unittest.TestCase):
    """Valid events → exit 0 / empty error list.

    Satisfies AC 2: covers representative event_types including one with a
    per-type payload schema (task_started).
    """

    def setUp(self) -> None:
        ve._PER_TYPE_CACHE.clear()

    def _assert_validates(self, event: dict) -> None:
        validator = ve.load_validator()
        errors = ve.validate_line(validator, "<test>", 1, json.dumps(event))
        self.assertEqual(errors, [], f"expected no errors; got {errors}")

    # Representative event_types

    def test_task_completed_is_valid(self) -> None:
        self._assert_validates(_valid_event(event_type="task_completed"))

    def test_task_blocked_is_valid(self) -> None:
        self._assert_validates(_valid_event(event_type="task_blocked"))

    def test_feature_created_is_valid(self) -> None:
        self._assert_validates(_valid_event(event_type="feature_created"))

    def test_plan_ready_is_valid(self) -> None:
        self._assert_validates(_valid_event(event_type="plan_ready"))

    def test_spec_validated_is_valid(self) -> None:
        self._assert_validates(_valid_event(event_type="spec_validated"))

    def test_human_escalation_is_valid(self) -> None:
        self._assert_validates(_valid_event(event_type="human_escalation"))

    def test_task_graph_drafted_is_valid(self) -> None:
        self._assert_validates(_valid_event(event_type="task_graph_drafted"))

    def test_override_applied_is_valid(self) -> None:
        self._assert_validates(_valid_event(event_type="override_applied"))

    def test_escalation_resolved_is_valid(self) -> None:
        self._assert_validates(_valid_event(event_type="escalation_resolved"))

    # task_started has a per-type payload schema; satisfy it.

    def test_task_started_with_valid_payload_is_valid(self) -> None:
        self._assert_validates(_valid_event(
            event_type="task_started",
            source="component:loop",
            payload={
                "issue_url": "https://github.com/owner/repo/issues/42",
                "branch": "feat/T01",
            },
        ))

    def test_task_started_with_null_branch_is_valid(self) -> None:
        self._assert_validates(_valid_event(
            event_type="task_started",
            source="component:loop",
            payload={
                "issue_url": "https://github.com/owner/repo/issues/1",
                "branch": None,
            },
        ))

    # Various valid source values

    def test_source_specs(self) -> None:
        self._assert_validates(_valid_event(source="specs"))

    def test_source_pm(self) -> None:
        self._assert_validates(_valid_event(source="pm"))

    def test_source_qa(self) -> None:
        self._assert_validates(_valid_event(source="qa"))

    def test_source_config_steward(self) -> None:
        self._assert_validates(_valid_event(source="config-steward"))

    def test_source_merge_watcher(self) -> None:
        self._assert_validates(_valid_event(source="merge-watcher"))

    def test_source_component(self) -> None:
        self._assert_validates(_valid_event(source="component:api-sample"))

    # end-to-end: main() exits 0

    def test_main_stdin_exits_0(self) -> None:
        rc, stdout, stderr = _call_main([], stdin_data=_valid_json())
        self.assertEqual(rc, 0, f"expected exit 0; stderr={stderr!r}")
        self.assertIn("ok:", stdout)

    def test_main_explicit_stdin_flag_exits_0(self) -> None:
        rc, stdout, stderr = _call_main(["--stdin"], stdin_data=_valid_json())
        self.assertEqual(rc, 0, f"expected exit 0; stderr={stderr!r}")

    def test_main_file_mode_exits_0(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(_valid_json(event_type="task_created") + "\n")
            f.write(_valid_json(event_type="task_ready") + "\n")
            fname = f.name
        try:
            rc, stdout, stderr = _call_main(["--file", fname])
            self.assertEqual(rc, 0, f"stderr={stderr!r}")
            self.assertIn("ok:", stdout)
        finally:
            Path(fname).unlink(missing_ok=True)

    def test_regression_envelope_mirroring_feat_0008(self) -> None:
        """Regression: envelope shape from FEAT-2026-0008 is valid when source
        is corrected from 'driver' to a schema-admitted value.

        Satisfies LEARNINGS [FEAT-2026-0005/G1-LESSONS] (regression case on
        existing valid fixture). Confirms the envelope itself is fine and that
        only the source value is what makes driver events invalid.
        """
        self._assert_validates(_valid_event(
            event_type="task_started",
            source="human",
            source_version="0.2.0",
            correlation_id="FEAT-2026-0008/T01",
            payload={
                "issue_url": "https://github.com/owner/repo/issues/1",
                "branch": None,
            },
        ))


class TestValidateEventInvalid(unittest.TestCase):
    """Invalid events → non-zero exit; error message names the offending key.

    Satisfies AC 3: covers (a) missing required key, (b) wrong type, (c)
    unknown event_type, (d) malformed JSON.
    Satisfies AC 4: driver event from FEAT-2026-0008 is rejected.
    """

    def setUp(self) -> None:
        ve._PER_TYPE_CACHE.clear()

    def _assert_rejected(
        self, event: dict | str, *, names_key: str = ""
    ) -> list[str]:
        raw = json.dumps(event) if isinstance(event, dict) else event
        validator = ve.load_validator()
        errors = ve.validate_line(validator, "<test>", 1, raw)
        self.assertTrue(errors, f"expected validation errors for {raw!r}")
        if names_key:
            combined = " ".join(errors)
            self.assertIn(
                names_key, combined,
                f"expected {names_key!r} named in errors={errors!r}",
            )
        return errors

    # (a) missing required key per event_type

    def test_missing_source_is_rejected(self) -> None:
        ev = _valid_event()
        del ev["source"]
        self._assert_rejected(ev, names_key="source")

    def test_missing_timestamp_is_rejected(self) -> None:
        ev = _valid_event()
        del ev["timestamp"]
        self._assert_rejected(ev, names_key="timestamp")

    def test_missing_payload_is_rejected(self) -> None:
        ev = _valid_event()
        del ev["payload"]
        self._assert_rejected(ev, names_key="payload")

    def test_missing_event_type_is_rejected(self) -> None:
        ev = _valid_event()
        del ev["event_type"]
        self._assert_rejected(ev, names_key="event_type")

    def test_missing_correlation_id_is_rejected(self) -> None:
        ev = _valid_event()
        del ev["correlation_id"]
        self._assert_rejected(ev, names_key="correlation_id")

    def test_missing_source_version_is_rejected(self) -> None:
        ev = _valid_event()
        del ev["source_version"]
        self._assert_rejected(ev, names_key="source_version")

    # (b) wrong type for a known key

    def test_payload_wrong_type_is_rejected(self) -> None:
        self._assert_rejected(
            _valid_event(payload="not-an-object"), names_key="payload"
        )

    def test_source_version_wrong_type_is_rejected(self) -> None:
        self._assert_rejected(
            _valid_event(source_version=42), names_key="source_version"
        )

    def test_correlation_id_wrong_type_is_rejected(self) -> None:
        self._assert_rejected(
            _valid_event(correlation_id=12345), names_key="correlation_id"
        )

    # (c) unknown event_type

    def test_unknown_event_type_is_rejected(self) -> None:
        self._assert_rejected(
            _valid_event(event_type="totally_unknown_type"),
            names_key="event_type",
        )

    # (d) malformed JSON line

    def test_malformed_json_line_is_rejected(self) -> None:
        validator = ve.load_validator()
        errors = ve.validate_line(validator, "<test>", 1, "not valid json {{")
        self.assertTrue(errors, "malformed JSON must produce errors")
        self.assertIn("invalid JSON", errors[0])

    # per-type payload: task_started missing required field

    def test_task_started_missing_issue_url_is_rejected(self) -> None:
        errors = self._assert_rejected(
            _valid_event(
                event_type="task_started",
                source="component:loop",
                payload={"branch": "feat/T01"},  # missing issue_url
            ),
            names_key="issue_url",
        )
        combined = " ".join(errors)
        self.assertIn("payload", combined)

    # end-to-end: main() exits 1

    def test_main_exits_1_on_invalid_source(self) -> None:
        rc, _, stderr = _call_main(
            [], stdin_data=json.dumps(_valid_event(source="driver"))
        )
        self.assertEqual(rc, 1, f"expected exit 1; stderr={stderr!r}")
        self.assertIn("source", stderr)

    # AC 4: driver events from FEAT-2026-0008 are rejected

    def test_driver_event_from_feat_0008_is_rejected(self) -> None:
        """Driver events (source: driver) must be rejected — documented contract.

        Reads a real event line from FEAT-2026-0008/events.jsonl and asserts
        the script rejects it with an error naming 'source'. loop.py emits
        source: "driver" which is intentionally NOT in the orchestrator's source
        enum. If the schema is later widened to admit "driver", this test must
        be updated in the same change — that coupling is intentional.
        """
        with open(FEAT_0008_EVENTS, encoding="utf-8") as fh:
            driver_line = next(
                line.strip()
                for line in fh
                if line.strip() and json.loads(line).get("source") == "driver"
            )
        validator = ve.load_validator()
        errors = ve.validate_line(
            validator, FEAT_0008_EVENTS.name, 1, driver_line
        )
        self.assertTrue(
            errors,
            "driver-emitted event must be rejected by the orchestrator schema",
        )
        combined = " ".join(errors)
        self.assertIn(
            "source", combined,
            f"rejection must name the 'source' key; errors={errors!r}",
        )

    # non-dict JSON: exercises the isinstance(event, dict) False branch

    def test_json_array_is_rejected(self) -> None:
        validator = ve.load_validator()
        errors = ve.validate_line(validator, "<test>", 1, "[1, 2, 3]")
        self.assertTrue(errors, "JSON array must fail object-type check")


class TestValidateEventSetupErrors(unittest.TestCase):
    """Exit-2 paths: missing schema, bad args, missing file, empty stdin."""

    def setUp(self) -> None:
        ve._PER_TYPE_CACHE.clear()

    def test_missing_schema_exits_2(self) -> None:
        with mock.patch.object(
            ve, "SCHEMA_PATH", Path("/nonexistent/event.schema.json")
        ):
            err = io.StringIO()
            with mock.patch("sys.stderr", err):
                with self.assertRaises(SystemExit) as ctx:
                    ve.load_validator()
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("schema not found", err.getvalue())

    def test_iter_lines_missing_file_exits_2(self) -> None:
        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            with self.assertRaises(SystemExit) as ctx:
                ve.iter_lines_from_file(Path("/nonexistent/events.jsonl"))
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("file not found", err.getvalue())

    def test_iter_lines_from_stdin_empty_exits_2(self) -> None:
        err = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO("   \n")):
            with mock.patch("sys.stderr", err):
                with self.assertRaises(SystemExit) as ctx:
                    ve.iter_lines_from_stdin()
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("no input on stdin", err.getvalue())

    def test_main_mutually_exclusive_exits_2(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".jsonl") as f:
            rc, _, stderr = _call_main(["--file", f.name, "--stdin"])
        self.assertEqual(rc, 2)
        self.assertIn("mutually exclusive", stderr)

    def test_main_unsupported_positional_exits_2(self) -> None:
        rc, _, stderr = _call_main(["unexpected-arg"])
        self.assertEqual(rc, 2)
        self.assertIn("unsupported argument", stderr)

    def test_main_empty_stdin_exits_2(self) -> None:
        rc, _, stderr = _call_main([], stdin_data="")
        self.assertEqual(rc, 2)
        self.assertIn("no input on stdin", stderr)


class TestFormatError(unittest.TestCase):
    """Unit tests for format_error(); covers both line_number branches."""

    def test_with_line_number_and_path(self) -> None:
        result = ve.format_error("source.jsonl", 5, "key", "bad value")
        self.assertEqual(result, "source.jsonl:5 at key: bad value")

    def test_without_line_number(self) -> None:
        # line_number=0 is falsy → location is bare source name.
        result = ve.format_error("source.jsonl", 0, "key", "bad value")
        self.assertEqual(result, "source.jsonl at key: bad value")

    def test_with_empty_path(self) -> None:
        # Empty path → no "at <path>" segment.
        result = ve.format_error("source.jsonl", 3, "", "some error")
        self.assertEqual(result, "source.jsonl:3: some error")


class TestLoadPerTypeValidator(unittest.TestCase):
    """Edge cases for load_per_type_validator(): caching and error paths."""

    def setUp(self) -> None:
        ve._PER_TYPE_CACHE.clear()

    def test_returns_validator_for_known_type(self) -> None:
        result = ve.load_per_type_validator("task_started")
        self.assertIsNotNone(result)

    def test_returns_none_for_unknown_type(self) -> None:
        result = ve.load_per_type_validator("no_such_event_type_xyz_abc")
        self.assertIsNone(result)

    def test_caches_result_on_second_call(self) -> None:
        v1 = ve.load_per_type_validator("task_started")
        v2 = ve.load_per_type_validator("task_started")
        self.assertIs(v1, v2)

    def test_none_result_is_also_cached(self) -> None:
        ve.load_per_type_validator("no_such_type_abc123")
        self.assertIn("no_such_type_abc123", ve._PER_TYPE_CACHE)
        self.assertIsNone(ve._PER_TYPE_CACHE["no_such_type_abc123"])

    def test_invalid_json_per_type_schema_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_dir = Path(tmpdir)
            (bad_dir / "bad_event.schema.json").write_text(
                "this is not json {{ garbage", encoding="utf-8"
            )
            err = io.StringIO()
            with (
                mock.patch.object(ve, "PER_TYPE_SCHEMA_DIR", bad_dir),
                mock.patch("sys.stderr", err),
            ):
                with self.assertRaises(SystemExit) as ctx:
                    ve.load_per_type_validator("bad_event")
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("failed to read per-type schema", err.getvalue())

    def test_invalid_schema_content_exits_2(self) -> None:
        # Valid JSON but not a valid JSON Schema.
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_dir = Path(tmpdir)
            (bad_dir / "bad_schema.schema.json").write_text(
                json.dumps({"type": 12345}), encoding="utf-8"
            )
            err = io.StringIO()
            with (
                mock.patch.object(ve, "PER_TYPE_SCHEMA_DIR", bad_dir),
                mock.patch("sys.stderr", err),
            ):
                with self.assertRaises(SystemExit) as ctx:
                    ve.load_per_type_validator("bad_schema")
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("invalid per-type schema", err.getvalue())


class TestIterLines(unittest.TestCase):
    """Unit tests for iter_lines_from_file and iter_lines_from_stdin."""

    def test_iter_lines_from_file_returns_non_blank(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(_valid_json() + "\n")
            f.write("   \n")  # blank — must be skipped
            f.write(_valid_json(event_type="task_blocked") + "\n")
            fname = f.name
        try:
            lines = ve.iter_lines_from_file(Path(fname))
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0][0], 1)
            self.assertEqual(lines[1][0], 3)
        finally:
            Path(fname).unlink(missing_ok=True)

    def test_iter_lines_from_stdin_skips_blank(self) -> None:
        data = (
            _valid_json() + "\n"
            + "\n"
            + _valid_json(event_type="plan_ready") + "\n"
        )
        with mock.patch("sys.stdin", io.StringIO(data)):
            lines = ve.iter_lines_from_stdin()
        self.assertEqual(len(lines), 2)

    def test_iter_lines_from_stdin_single_line(self) -> None:
        with mock.patch("sys.stdin", io.StringIO(_valid_json() + "\n")):
            lines = ve.iter_lines_from_stdin()
        self.assertEqual(len(lines), 1)


class TestResolveSchemaRoot(unittest.TestCase):
    """_resolve_schema_root covers the env var branch and the sibling fallback."""

    def test_env_var_path_used_when_set(self) -> None:
        with mock.patch.dict(os.environ, {"SPECFUSE_SCHEMA_ROOT": "/some/path"}):
            result = ve._resolve_schema_root()
        self.assertEqual(result, Path("/some/path").resolve())

    def test_sibling_fallback_used_when_env_absent(self) -> None:
        env_without = {
            k: v
            for k, v in os.environ.items()
            if k != "SPECFUSE_SCHEMA_ROOT"
        }
        with mock.patch.dict(os.environ, env_without, clear=True):
            result = ve._resolve_schema_root()
        expected = (
            Path(SCRIPT).resolve().parent.parent.parent.parent
            / "orchestrator"
            / "shared"
            / "schemas"
        )
        self.assertEqual(result, expected)


class TestValidateEventSubprocess(unittest.TestCase):
    """End-to-end subprocess tests preserving the exit-code contract.

    These do NOT contribute to in-process coverage; they exist to prove the
    script is invocable as a CLI and exits with the right codes.
    """

    def _run(
        self,
        args: list[str],
        stdin_text: str | None = None,
        schema_root: str | None = None,
    ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        if schema_root is not None:
            env["SPECFUSE_SCHEMA_ROOT"] = schema_root
        return subprocess.run(
            [sys.executable, str(SCRIPT)] + args,
            input=stdin_text,
            capture_output=True,
            text=True,
            env=env,
        )

    def test_cli_exits_0_on_valid_stdin(self) -> None:
        proc = self._run([], stdin_text=_valid_json())
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_cli_exits_1_on_invalid_source(self) -> None:
        proc = self._run(
            [],
            stdin_text=json.dumps(_valid_event(source="driver")),
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("source", proc.stderr)

    def test_cli_exits_2_on_missing_schema(self) -> None:
        proc = self._run(
            [],
            stdin_text=_valid_json(),
            schema_root="/nonexistent/schemas",
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("schema not found", proc.stderr)


if __name__ == "__main__":
    unittest.main()
