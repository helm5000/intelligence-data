"""Read Roll Call Factbase social activity without storing any posts or using a database."""
import datetime as dt
import json
import sys
from pathlib import Path

import requests

API_URL = "https://rollcall.com/api/factbase/social"
SOURCE = "Roll Call Factbase (Truth Social + X/Twitter)"


def parse_snapshot(payload, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    meta = payload.get("meta")
    rows = payload.get("data")
    stats = payload.get("stats")
    if not isinstance(meta, dict) or not isinstance(rows, list) or not isinstance(stats, dict):
        raise ValueError("Factbase response schema changed")
    total_hits = meta.get("total_hits")
    if not isinstance(total_hits, int) or total_hits < 1 or not rows:
        raise ValueError("Factbase returned no indexed posts; refusing a false zero")

    period = stats.get("date_range", {}).get("last_hour")
    if not isinstance(period, dict):
        raise ValueError("Missing last_hour statistics")
    total = period.get("total")
    platforms = period.get("platform")
    if not isinstance(total, int) or total < 0 or not isinstance(platforms, dict):
        raise ValueError("Malformed last_hour statistics")
    truth = platforms.get("truth_social")
    x_count = platforms.get("x_twitter")
    if (not isinstance(truth, int) or not isinstance(x_count, int)
            or truth < 0 or x_count < 0 or total != truth + x_count):
        raise ValueError("Inconsistent last_hour totals/platform breakdown")

    dates = []
    for row in rows:
        date_str = row.get("date") if isinstance(row, dict) else None
        if not date_str:
            continue
        try:
            posted = dt.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if posted.tzinfo is not None:
                dates.append(posted.astimezone(dt.timezone.utc))
        except (TypeError, ValueError):
            continue
    if not dates:
        raise ValueError("No valid, timezone-aware post timestamps")

    latest = max(dates)
    age = (now - latest).total_seconds()
    if age < -300:
        raise ValueError("Latest post is more than 5 min in the future")
    return {
        "postCount": total,
        "minutesSince": max(0, int(age // 60)),
        "status": "live",
        "source": SOURCE,
        "lastUpdated": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "platformCounts": {"truth_social": truth, "x_twitter": x_count},
        "lastPostAt": latest.isoformat(),
    }


def main():
    try:
        response = requests.get(
            API_URL,
            headers={"User-Agent": "intelligence-data/1.0 (public activity counter)",
                     "Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        snapshot = parse_snapshot(response.json())
    except (requests.RequestException, ValueError, TypeError, KeyError) as err:
        print(f"DATA ERROR: {err} -- will not replace last verified snapshot", file=sys.stderr)
        return 1

    print("VERIFIED Factbase:", json.dumps(snapshot, ensure_ascii=False), flush=True)
    if "--dry-run" in sys.argv:
        return 0
    path = Path("data.json")
    staged = Path("data.json.tmp")
    staged.write_text(json.dumps(snapshot, ensure_ascii=False) + "\n", encoding="utf-8")
    staged.replace(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
