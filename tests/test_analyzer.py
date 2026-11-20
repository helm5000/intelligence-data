import datetime as dt
import unittest

from analyzer import parse_snapshot


NOW = dt.datetime(2026, 11, 20, 14, 54, tzinfo=dt.timezone.utc)


def example(total=3, truth=2, twitter=1, date="2026-11-20T09:45:00-05:00"):
    return {
        "meta": {"total_hits": 98372},
        "data": [{"date": date, "platform": "Truth Social", "id": "12345"}],
        "stats": {"date_range": {"last_hour": {
            "total": total, "platform": {"truth_social": truth, "x_twitter": twitter}
        }}},
    }


class CountTests(unittest.TestCase):
    def test_multiplatform_totals_and_timezone(self):
        record = parse_snapshot(example(), NOW)
        self.assertEqual(record["postCount"], 3)
        self.assertEqual(record["minutesSince"], 9)
        self.assertEqual(record["platformCounts"], {"truth_social": 2, "x_twitter": 1})

    def test_legitimate_zero(self):
        record = parse_snapshot(example(0, 0, 0, "2026-11-20T08:03:00-05:00"), NOW)
        self.assertEqual(record["postCount"], 0)
        self.assertEqual(record["minutesSince"], 111)

    def test_inconsistent_aggregate_is_failure(self):
        with self.assertRaises(ValueError):
            parse_snapshot(example(99, 2, 1), NOW)

    def test_empty_data_is_failure(self):
        payload = example()
        payload["data"] = []
        with self.assertRaises(ValueError):
            parse_snapshot(payload, NOW)

    def test_timezone_missing_is_failure(self):
        with self.assertRaises(ValueError):
            parse_snapshot(example(date="2026-11-20T09:45:00"), NOW)


if __name__ == "__main__":
    unittest.main()
