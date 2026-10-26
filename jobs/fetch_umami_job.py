# jobs/fetch_umami_job.py
# top of fetch_umami_job.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, UTC
import os
from app.services.normalizers.country import normalize_countries
from app.services.normalizers.region import normalize_regions
from app.database import collection
from app.services.umami_client import fetch_metrics, fetch_stats, fetch_traffic
from app.services.processor import compute_extra_metrics
from app.utils.range_mapper import get_umami_range

print("Running fetch_umami_job.py from:", os.path.abspath(__file__))

WEBSITE_ID = os.getenv("UMAMI_WEBSITE_ID", "")
if not WEBSITE_ID:
    raise RuntimeError("UMAMI_WEBSITE_ID not found in .env")

RANGES = ["24h", "7d", "30d", "90d", "1y"]

# Map each range to the traffic unit for Umami API
UNIT_MAP = {
    "24h": "hour",
    "7d": "day",
    "30d": "day",
    "90d": "day",
    "1y": "month"
}

def run():
    # Container for all ranges
    all_ranges = {}

    for range_key in RANGES:
        start_at, end_at = get_umami_range(range_key)

        # --------------------------
        # 1️⃣ Fetch stats & extra metrics
        # --------------------------
        stats = fetch_stats(WEBSITE_ID, start_at, end_at)
        extra = compute_extra_metrics(stats)

        # --------------------------
        # 2️⃣ Build metrics dict
        # --------------------------
        metrics = {
            "pages": [{"url": i["x"], "count": i["y"]} for i in fetch_metrics(WEBSITE_ID, "url", start_at, end_at)],
            "referrers": [{"referrer": i["x"], "count": i["y"]} for i in fetch_metrics(WEBSITE_ID, "referrer", start_at, end_at)],
            "devices": [{"device": i["x"], "count": i["y"]} for i in fetch_metrics(WEBSITE_ID, "device", start_at, end_at)],
            "countries": normalize_countries(fetch_metrics(WEBSITE_ID, "country", start_at, end_at)),
            "regions": normalize_regions(fetch_metrics(WEBSITE_ID, "region", start_at, end_at)),
            "browsers": [{"browser": i["x"], "count": i["y"]} for i in fetch_metrics(WEBSITE_ID, "browser", start_at, end_at)],
            "os": [{"os": i["x"], "count": i["y"]} for i in fetch_metrics(WEBSITE_ID, "os", start_at, end_at)],
        }

        # --------------------------
        # 3️⃣ Fetch traffic over time
        # --------------------------
        unit = UNIT_MAP[range_key]
        traffic = fetch_traffic(WEBSITE_ID, unit, start_at, end_at)

        # Map x -> y for easy plotting/storage
        pv_map = {i["x"]: i["y"] for i in traffic.get("pageviews", [])}
        s_map = {i["x"]: i["y"] for i in traffic.get("sessions", [])}
        times = sorted(set(pv_map) | set(s_map))
        views = [pv_map.get(t, 0) for t in times]
        visits = [s_map.get(t, 0) for t in times]

        # --------------------------
        # 4️⃣ Store everything in all_ranges
        # --------------------------
        all_ranges[range_key] = {
            "start_at": start_at,
            "end_at": end_at,
            "metrics": metrics,
            "stats": {**stats, "comparison": stats.get("comparison", {})},
            "bounce_rate": extra.get("bounce_rate"),
            "average_duration": extra.get("average_duration"),
            "traffic": {
                "times": times,
                "views": views,
                "visits": visits
            }
        }

        # --------------------------
        # 5️⃣ Logging
        # --------------------------
        print(f"Range {range_key} → sample pages:", metrics["pages"][:2])
        print(f"Range {range_key} → sample traffic:", all_ranges[range_key]["traffic"])

    # --------------------------
    # 6️⃣ Store ONE document for all ranges
    # --------------------------
    collection.update_one(
        {"website_id": WEBSITE_ID},
        {
            "$set": {
                "website_id": WEBSITE_ID,
                "updated_at": datetime.now(UTC),
                "ranges": all_ranges
            }
        },
        upsert=True
    )

    print("✅ Umami snapshot refreshed → ALL ranges updated")

if __name__ == "__main__":
    run()
