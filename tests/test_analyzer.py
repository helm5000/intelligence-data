import datetime as dt
import unittest

from analyzer import parse_feed


NOW = dt.datetime(2026, 11, 20, 14, 30, tzinfo=dt.timezone.utc)


def rss(items):
    return ("<rss version='2.0'><channel>" + items + "</channel></rss>").encode()


def item(identifier, when):
    return f"<item><guid>{identifier}</guid><pubDate>{when}</pubDate></item>"


class ParseFeedTests(unittest.TestCase):
    def test_recent_old_and_duplicates(self):
        feed = rss(
            item("a", "Fri, 20 Nov 2026 14:20:00 +0000")
            + item("a", "Fri, 20 Nov 2026 14:20:00 +0000")
            + item("b", "Fri, 20 Nov 2026 13:31:00 +0000")
            + item("c", "Fri, 20 Nov 2026 13:30:00 +0000")
        )
        result = parse_feed(feed, NOW)
        self.assertEqual(result["postCount"], 2)
        self.assertEqual(result["minutesSince"], 10)
        self.assertEqual(result["status"], "live")

    def test_old_posts_are_not_fabricated(self):
        result = parse_feed(rss(item("x", "Thu, 19 Nov 2026 11:00:00 -0500")), NOW)
        self.assertEqual(result["postCount"], 0)
        self.assertEqual(result["minutesSince"], 1350)

    def test_empty_feed_is_failure(self):
        with self.assertRaises(ValueError):
            parse_feed(rss(""), NOW)

    def test_invalid_timestamps_are_failure(self):
        with self.assertRaises(ValueError):
            parse_feed(rss(item("x", "bogus")), NOW)


if __name__ == "__main__":
    unittest.main()
