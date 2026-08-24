# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The umbrella coordinate is resolved and validated, not asserted (#2757).

`## [X.Y.Z+umbrella.A.B.C]` was true for ten releases and then silently was
not: `0.13.0+umbrella.0.13.0` and `0.14.0+umbrella.0.14.0` both name umbrella
versions that were never published. The old check tested `--umbrella-version`
for non-emptiness and nothing else, so a fiction and a fact were
indistinguishable to it.

Every test here injects `fetch`, so the suite never touches PyPI. A test that
reached the real index would be slow, would fail offline, and would change its
answer whenever the umbrella released -- turning a deterministic check into a
weather report.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_spec = importlib.util.spec_from_file_location(
    "_bump_version_umbrella", _REPO_ROOT / "scripts" / "bump_version.py"
)
bump = importlib.util.module_from_spec(_spec)
# Registered before exec: the module defines a @dataclass, and dataclasses
# resolves the defining module via sys.modules[cls.__module__] at decoration
# time -- absent, decoration raises rather than the test failing informatively.
sys.modules[_spec.name] = bump
_spec.loader.exec_module(bump)

#: The real shape at the time of #2757: umbrella stopped at 0.12.1 while the
#: driver went on to 0.13.0 and 0.14.0.
RELEASED = ("0.11.0", "0.12.0", "0.12.1")


def _fetch_ok():
    return RELEASED


def _fetch_down():
    raise bump.UmbrellaUnreachable("connection refused")


class TestResolutionFromTheIndex(unittest.TestCase):
    def test_omitted_resolves_to_the_latest_release(self):
        version, verified = bump.resolve_umbrella_version(None, fetch=_fetch_ok)

        self.assertEqual(version, "0.12.1")
        self.assertTrue(verified)

    def test_an_explicit_released_version_is_accepted_and_verified(self):
        version, verified = bump.resolve_umbrella_version("0.12.0", fetch=_fetch_ok)

        self.assertEqual(version, "0.12.0")
        self.assertTrue(verified)

    def test_a_version_never_released_is_rejected(self):
        """The exact defect: 0.14.0 was accepted and does not exist."""
        with self.assertRaises(ValueError) as ctx:
            bump.resolve_umbrella_version("0.14.0", fetch=_fetch_ok)

        message = str(ctx.exception)
        self.assertIn("never been released", message)
        self.assertIn("0.12.1", message, "the error must name what does exist")

    def test_the_two_published_wrong_headings_would_now_fail(self):
        for bogus in ("0.13.0", "0.14.0"):
            with self.subTest(umbrella=bogus):
                with self.assertRaises(ValueError):
                    bump.resolve_umbrella_version(bogus, fetch=_fetch_ok)


class TestUnreachableIsNotTheSameAsAbsent(unittest.TestCase):
    """Conflating "could not look" with "not there" is how a check reports a
    wrong answer instead of no answer."""

    def test_an_outage_does_not_reject_a_passed_version(self):
        version, verified = bump.resolve_umbrella_version("0.12.1", fetch=_fetch_down)

        self.assertEqual(version, "0.12.1")
        self.assertFalse(verified, "it must be flagged as unverified, not silently trusted")

    def test_an_outage_with_nothing_to_fall_back_on_raises(self):
        """There is no value to write, so inventing one is the only wrong move."""
        with self.assertRaises(bump.UmbrellaUnreachable):
            bump.resolve_umbrella_version(None, fetch=_fetch_down)

    def test_an_outage_never_silently_yields_a_wrong_version(self):
        """A release must not be blocked by a documentation field, but it must
        also never record a fiction as fact -- so the only path through an
        outage is the explicitly-passed one, flagged."""
        _version, verified = bump.resolve_umbrella_version("9.9.9", fetch=_fetch_down)

        self.assertFalse(verified)


class TestFetchFailsClosedOnBadPayloads(unittest.TestCase):
    def test_empty_release_set_is_unreachable_not_empty(self):
        """An empty tuple would mean "no such release" to the caller, which
        would reject every valid version on a malformed response."""
        import json
        import io
        import contextlib

        class _Resp(io.StringIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def _urlopen(url, timeout=None):
            return _Resp(json.dumps({"releases": {}}))

        with contextlib.ExitStack() as stack:
            stack.enter_context(_patched(bump.urllib.request, "urlopen", _urlopen))
            with self.assertRaises(bump.UmbrellaUnreachable):
                bump.fetch_umbrella_versions("https://example.com/x")

    def test_unparseable_payload_is_unreachable(self):
        import contextlib
        import io

        class _Resp(io.StringIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def _urlopen(url, timeout=None):
            return _Resp("not json")

        with contextlib.ExitStack() as stack:
            stack.enter_context(_patched(bump.urllib.request, "urlopen", _urlopen))
            with self.assertRaises(bump.UmbrellaUnreachable):
                bump.fetch_umbrella_versions("https://example.com/x")


class _patched:
    """Minimal attribute patcher — avoids a unittest.mock import for two uses."""

    def __init__(self, obj, name, value):
        self._obj, self._name, self._value = obj, name, value

    def __enter__(self):
        self._prior = getattr(self._obj, self._name)
        setattr(self._obj, self._name, self._value)
        return self._value

    def __exit__(self, *_a):
        setattr(self._obj, self._name, self._prior)
        return False


class TestReleaseStillRefusesAnEmptyCoordinate(unittest.TestCase):
    def test_release_rejects_empty_umbrella_version(self):
        """`release()` is a library entry point; resolution is the caller's
        job, but it must not stamp a blank coordinate if one slips through."""
        with self.assertRaises(ValueError):
            bump.release(_REPO_ROOT, "9.9.9", "")


if __name__ == "__main__":
    unittest.main()
