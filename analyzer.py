"""Produce a verifiable Truth Social activity snapshot from Trump's Truth RSS."""

import datetime as dt
import json
import os
import sys
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

FEED_URL = "https://www.trumpstruth.org/feed"
SOURCE_NAME = "Trump's Truth (Truth Social)"


def parse_feed(xml_body: bytes, now: dt.datetime) -> dict:
    """Return counts based on RSS pubDate (original posting time, not polling time)."""
    root = ET.fromstring(xml_body)
    items = root.findall("./channel/item")
    if not items:
        raise ValueError("RSS response contains no items; refusing to publish a false zero")

    seen = set()
    ages_minutes = []
    for item in items:
        identifier = item.findtext("guid") or item.findtext("link")
        if identifier and identifier in seen:
            continue
        if identifier:
            seen.add(identifier)

        date_text = item.findtext("pubDate")
        if not date_text:
            continue
        try:
            posted_at = parsedate_to_datetime(date_text)
            if posted_at.tzinfo is None:
                continue
        except (TypeError, ValueError, IndexError):
            continue

        diff_seconds = (now - posted_at.astimezone(dt.timezone.utc)).total_seconds()
        if diff_seconds < -300:
            continue
        ages_minutes.append(max(0, int(diff_seconds // 60)))

    if not ages_minutes:
        raise ValueError("RSS response has no parsable posting timestamps")

    return {
        "postCount": sum(minutes < 60 for minutes in ages_minutes),
        "minutesSince": min(ages_minutes),
        "status": "live",
        "source": SOURCE_NAME,
        "lastUpdated": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def main() -> int:
    try:
        response = requests.get(
            FEED_URL,
            params={"limit": "500"},
            headers={
                "User-Agent": "intelligence-data/1.0 (public RSS activity monitor)",
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
            timeout=30,
        )
        response.raise_for_status()
        result = parse_feed(response.content, dt.datetime.now(dt.timezone.utc))
    except (requests.RequestException, ET.ParseError, ValueError) as exc:
        print(f"DATA SOURCE ERROR: {exc}; existing data.json left unchanged", file=sys.stderr)
        return 1

    destination = Path("data.json")
    temporary = Path("data.json.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, destination)
    print(f"SOURCE OK: {result['source']}; {result['postCount']} posts in last hour; latest {result['minutesSince']} minutes ago")
    return 0


if __name__ == "__main__":
    sys.exit(main())
