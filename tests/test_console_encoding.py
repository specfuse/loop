# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# FEAT-2026-0032: the driver prints non-ASCII console glyphs (↳, ═, ⚠, —).
# On Windows the default console codepage is cp1252, which cannot encode them,
# so an unguarded run dies with UnicodeEncodeError the moment it prints a WU
# title. Caught by the windows-latest CI leg (T04). main() calls
# _force_utf8_console() to reconfigure stdout/stderr to UTF-8; these tests are
# Linux-runnable — they simulate the cp1252 stream directly rather than needing
# a real Windows host.

import io
import unittest

from specfuse.loop import loop


# A driver glyph that is not encodable in cp1252.
_GLYPH = "↳"  # ↳


class TestConsoleEncoding(unittest.TestCase):
    def test_cp1252_stream_cannot_encode_driver_glyph(self):
        """Reproduce the Windows failure mode: a cp1252 text stream raises on ↳."""
        stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
        with self.assertRaises(UnicodeEncodeError):
            stream.write(_GLYPH)
            stream.flush()

    def test_reconfigure_to_utf8_lets_the_glyph_through(self):
        """The fix mechanism: after reconfigure(encoding='utf-8') the same
        stream encodes ↳ without error."""
        buf = io.BytesIO()
        stream = io.TextIOWrapper(buf, encoding="cp1252")
        stream.reconfigure(encoding="utf-8")
        stream.write(f"   {_GLYPH} title")
        stream.flush()
        self.assertIn(_GLYPH.encode("utf-8"), buf.getvalue())

    def test_force_utf8_console_reconfigures_both_streams(self):
        """_force_utf8_console reconfigures stdout AND stderr to utf-8."""
        calls = []

        class FakeStream:
            def reconfigure(self, **kw):
                calls.append(kw)

        import sys
        orig_out, orig_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = FakeStream(), FakeStream()
        try:
            loop._force_utf8_console()
        finally:
            sys.stdout, sys.stderr = orig_out, orig_err
        self.assertEqual(calls, [{"encoding": "utf-8"}, {"encoding": "utf-8"}])

    def test_force_utf8_console_tolerates_stream_without_reconfigure(self):
        """A replaced stream lacking reconfigure (e.g. a plain buffer) must not
        crash the driver at startup."""
        import sys
        orig_out, orig_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
        try:
            loop._force_utf8_console()  # must not raise
        finally:
            sys.stdout, sys.stderr = orig_out, orig_err


if __name__ == "__main__":
    unittest.main()
