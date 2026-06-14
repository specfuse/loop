#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""Calibration regression for gate_eval.py — FEAT-2026-0018/T03.

Pins predicate v1 behavior against the 4-feature backtest baseline
(0013, 0014, 0015, 0017). Any drift — predicate change OR feature-data
change — fails LOUDLY here.

Drift policy:
- Test fails because feature data evolved → data drift is the bug; the
  baseline IS the source of truth.
- Test fails because predicate was intentionally changed → update the
  baseline in the same commit and name the rationale in the commit message.
"""

from __future__ import annotations

import io
import sys
import unittest
import unittest.mock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_scripts = str(REPO_ROOT / ".specfuse/scripts")
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)

from gate_eval import (  # noqa: E402
    AutoCloseDecision,
    PREDICATE_VERSION,
    _format_decision,
    _resolve_feature_dir,
    evaluate_auto_close,
    main,
)

FEATURES_DIR = REPO_ROOT / ".specfuse" / "features"

# ---------------------------------------------------------------------------
# Pinned baseline
# Reason class = first colon-separated segment, e.g.
#   "per_wu_cost_overrun: T03 actual=..." → class "per_wu_cost_overrun"
# ---------------------------------------------------------------------------

CALIBRATION = {
    ("FEAT-2026-0013", 1): {
        "auto": False,
        "reason_classes": {"blocked_human_in_chain"},
    },
    ("FEAT-2026-0014", 1): {
        "auto": False,
        "reason_classes": {"blocked_human_in_chain"},
    },
    ("FEAT-2026-0015", 1): {
        "auto": False,
        "reason_classes": {
            "blocked_human_in_chain",
            "final_attempt_not_passed",
            "per_wu_cost_overrun",
            "per_wu_hard_overrun",
            "plan_next_overrun",
        },
    },
    ("FEAT-2026-0015", 2): {
        "auto": False,
        "reason_classes": {"per_wu_cost_overrun", "per_wu_hard_overrun"},
    },
    ("FEAT-2026-0017", 1): {
        "auto": False,
        "reason_classes": {
            "blocked_human_in_chain",
            "per_wu_cost_overrun",
            "per_wu_hard_overrun",
        },
    },
}

_FEATURE_SLUG = {
    "FEAT-2026-0013": "FEAT-2026-0013-ci-workspace-race-fix",
    "FEAT-2026-0014": "FEAT-2026-0014-gha-node20-bump",
    "FEAT-2026-0015": "FEAT-2026-0015-closing-ceremony-restructure",
    "FEAT-2026-0017": "FEAT-2026-0017-wiring-race-guard",
}


def _feature_dir(feat_id: str) -> Path:
    return FEATURES_DIR / _FEATURE_SLUG[feat_id]


def _reason_classes(reasons: list[str]) -> set[str]:
    return {r.split(":")[0].strip() for r in reasons}


def _make_test(feat_id: str, gate: int, expected: dict):
    fdir = _feature_dir(feat_id)

    @unittest.skipUnless(fdir.is_dir(), f"skipped: feature dir absent ({fdir.name})")
    def test_method(self):
        decision = evaluate_auto_close(fdir, gate)
        observed_auto = decision.auto
        observed_classes = _reason_classes(decision.reasons)

        errors = []
        if observed_auto != expected["auto"]:
            errors.append(
                f"auto mismatch: observed={observed_auto!r} expected={expected['auto']!r}"
            )
        if observed_classes != expected["reason_classes"]:
            only_observed = observed_classes - expected["reason_classes"]
            only_expected = expected["reason_classes"] - observed_classes
            if only_observed:
                errors.append(f"unexpected reason classes: {sorted(only_observed)}")
            if only_expected:
                errors.append(f"missing reason classes: {sorted(only_expected)}")

        if errors:
            self.fail(
                f"({feat_id}, gate={gate}) calibration drift:\n"
                + "\n".join(f"  {e}" for e in errors)
                + f"\nobserved reasons: {decision.reasons}"
                + f"\nexpected classes: {sorted(expected['reason_classes'])}"
            )

    return test_method


class TestCalibration(unittest.TestCase):
    pass


for (_feat_id, _gate), _expected in CALIBRATION.items():
    _method_name = f"test_{_feat_id.replace('-', '_')}_gate{_gate}"
    setattr(TestCalibration, _method_name, _make_test(_feat_id, _gate, _expected))


# ---------------------------------------------------------------------------
# Unit tests for CLI helpers (AC5, AC6)
# ---------------------------------------------------------------------------


def _make_decision(*, auto=True, reasons=None, gate_id=1, metrics=None):
    return AutoCloseDecision(
        auto=auto,
        reasons=reasons or [],
        metrics=metrics or {"gate_total_cost": 0.0, "gate_budget": None},
        gate_id=gate_id,
        feature_id="FEAT-2026-9999",
        predicate_version=PREDICATE_VERSION,
    )


class TestFormatDecision(unittest.TestCase):

    def test_auto_true_no_reasons_no_budget(self):
        d = _make_decision(auto=True)
        out = _format_decision(d)
        self.assertIn("G01  auto=True", out)
        self.assertNotIn("reasons:", out)
        self.assertIn("gate_total_cost: $0.00", out)
        self.assertIn("gate_budget: <unset>", out)

    def test_auto_false_with_reasons(self):
        d = _make_decision(
            auto=False,
            reasons=["blocked_human_in_chain: T01 escalated 2026-06-11"],
        )
        out = _format_decision(d)
        self.assertIn("auto=False", out)
        self.assertIn("reasons:", out)
        self.assertIn("- blocked_human_in_chain: T01 escalated 2026-06-11", out)

    def test_budget_shown_when_set(self):
        d = _make_decision(
            metrics={"gate_total_cost": 5.25, "gate_budget": 8.0},
        )
        out = _format_decision(d)
        self.assertIn("gate_total_cost: $5.25", out)
        self.assertIn("gate_budget: $8.00", out)

    def test_gate_id_zero_padded(self):
        d = _make_decision(gate_id=3)
        out = _format_decision(d)
        self.assertIn("G03  auto=", out)


class TestResolveFeatureDir(unittest.TestCase):

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        feat_root = self.tmp / ".specfuse" / "features"
        feat_root.mkdir(parents=True)
        (feat_root / "FEAT-2026-0099-my-slug").mkdir()
        (feat_root / "FEAT-2026-0100-other-slug").mkdir()
        (feat_root / "FEAT-2026-0101-shared").mkdir()
        (feat_root / "FEAT-2027-0101-shared-v2").mkdir()
        # Two dirs with same FEAT-YYYY-NNNN prefix → triggers prefix ambiguity
        (feat_root / "FEAT-2026-0200-alpha").mkdir()
        (feat_root / "FEAT-2026-0200-beta").mkdir()
        self.feat_root = feat_root

    def tearDown(self):
        self._tmp.cleanup()

    def test_full_feature_id_prefix_match(self):
        d = _resolve_feature_dir("FEAT-2026-0099", self.tmp)
        self.assertIsNotNone(d)
        self.assertEqual(d.name, "FEAT-2026-0099-my-slug")

    def test_partial_nnnn_match(self):
        d = _resolve_feature_dir("0100", self.tmp)
        self.assertIsNotNone(d)
        self.assertEqual(d.name, "FEAT-2026-0100-other-slug")

    def test_slug_match(self):
        d = _resolve_feature_dir("my-slug", self.tmp)
        self.assertIsNotNone(d)
        self.assertEqual(d.name, "FEAT-2026-0099-my-slug")

    def test_no_match_returns_none(self):
        d = _resolve_feature_dir("FEAT-9999-9999", self.tmp)
        self.assertIsNone(d)

    def test_ambiguous_nnnn_raises(self):
        with self.assertRaises(ValueError):
            _resolve_feature_dir("0101", self.tmp)

    def test_missing_features_dir_returns_none(self):
        import tempfile
        with tempfile.TemporaryDirectory() as empty:
            d = _resolve_feature_dir("anything", Path(empty))
        self.assertIsNone(d)

    def test_exact_dir_name_match(self):
        d = _resolve_feature_dir("FEAT-2026-0099-my-slug", self.tmp)
        self.assertIsNotNone(d)
        self.assertEqual(d.name, "FEAT-2026-0099-my-slug")

    def test_ambiguous_prefix_raises(self):
        # "FEAT-2026-0200" prefix-matches both alpha and beta dirs
        with self.assertRaises(ValueError):
            _resolve_feature_dir("FEAT-2026-0200", self.tmp)

    def test_short_dir_name_fallback(self):
        (self.feat_root / "nomatch").mkdir()
        (self.feat_root / "my-special").mkdir()
        d = _resolve_feature_dir("my-special", self.tmp)
        self.assertIsNotNone(d)
        self.assertEqual(d.name, "my-special")


_0017_DIR = FEATURES_DIR / "FEAT-2026-0017-wiring-race-guard"


class TestMainCLI(unittest.TestCase):

    def _run_main(self, argv):
        with unittest.mock.patch("sys.argv", ["gate_eval.py"] + argv):
            with unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                try:
                    main()
                except SystemExit:
                    pass
                return mock_out.getvalue()

    def test_no_args_prints_help_and_exits(self):
        with unittest.mock.patch("sys.argv", ["gate_eval.py"]):
            with unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 0)
                self.assertIn("backtest", mock_out.getvalue())

    def test_no_feature_match_exits_0(self):
        with unittest.mock.patch("sys.argv", ["gate_eval.py", "backtest", "FEAT-9999-9999"]):
            with unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 0)
                self.assertIn("no feature matches", mock_out.getvalue())

    @unittest.skipUnless(_0017_DIR.is_dir(), "skipped: feature dir absent (FEAT-2026-0017)")
    def test_backtest_0017_runs_and_prints_feature_id(self):
        out = self._run_main(["backtest", "0017"])
        self.assertIn("FEAT-2026-0017", out)
        self.assertIn("auto=", out)

    @unittest.skipUnless(_0017_DIR.is_dir(), "skipped: feature dir absent (FEAT-2026-0017)")
    def test_backtest_gate_filter(self):
        out = self._run_main(["backtest", "0017", "--gate", "1"])
        self.assertIn("G01", out)


if __name__ == "__main__":
    unittest.main()
