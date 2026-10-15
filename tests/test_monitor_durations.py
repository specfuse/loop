import unittest

from specfuse.monitor.durations import parse_duration_seconds
from specfuse.monitor.providers.azure_service_bus import parse_stall_after_seconds

ACCEPTED = {"30s": 30, "15m": 900, "2h": 7200, "1d": 86400, "90s": 90}
REJECTED = ("15", "15 minutes", "15min", "10 minutes", "m15", "", "-5m", " 5m")


class DurationGrammarTests(unittest.TestCase):
    def test_accepted_cases_agree(self):
        for value, seconds in ACCEPTED.items():
            with self.subTest(value=value):
                self.assertEqual(parse_duration_seconds(value), seconds)
                self.assertEqual(parse_stall_after_seconds(value), seconds)

    def test_rejected_cases_agree(self):
        for value in REJECTED:
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as a:
                    parse_duration_seconds(value)
                with self.assertRaises(ValueError) as b:
                    parse_stall_after_seconds(value)
                self.assertIn(repr(value), str(a.exception))
                self.assertEqual(str(a.exception), str(b.exception))


if __name__ == "__main__":
    unittest.main()
