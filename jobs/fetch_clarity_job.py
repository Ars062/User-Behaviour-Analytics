# python -m jobs.fetch_clarity_job

from datetime import datetime, timedelta, UTC
import requests
from urllib.parse import urlparse
import time

from app.database import clarity_collection
from app.config import CLARITY_PROJECT_TOKENS

# =========================
# CONSTANTS
# =========================

API_URL = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
RANGE_HOURS = 24

# =========================
# HELPERS
# =========================

def clean_url(url: str) -> str:
    if not url:
        return "/"
    return urlparse(url).path or "/"

# =========================
# NORMALIZER
# =========================

def normalize_clarity(raw):
    pages = {}

    def get_page(url):
        if url not in pages:
            pages[url] = {
                "traffic": {},
                "engagement": {},
                "behavioral_insights": {}
            }
        return pages[url]

    for metric in raw:
        name = metric.get("metricName")
        info = metric.get("information") or []

        for row in info:
            url = clean_url(row.get("Url"))
            page = get_page(url)

            if name == "Traffic":
                page["traffic"] = {
                    "sessions": int(row.get("totalSessionCount", 0)),
                    "users": int(row.get("distinctUserCount", 0)),
                    "bot_sessions": int(row.get("totalBotSessionCount", 0)),
                }

            elif name == "EngagementTime":
                page["engagement"] = {
                    "total_time_sec": int(row.get("totalTime", 0)),
                    "active_time_sec": int(row.get("activeTime", 0)),
                }

            elif name == "ScrollDepth":
                page.setdefault("engagement", {})
                page["engagement"]["avg_scroll_depth_pct"] = row.get("averageScrollDepth", 0)

            elif name in [
                "DeadClickCount", "RageClickCount", "QuickbackClick",
                "ExcessiveScroll", "ScriptErrorCount", "ErrorClickCount"
            ]:
                key = name.replace("Count", "").lower()
                page["behavioral_insights"][key] = {
                    "sessions": int(row.get("sessionsCount", 0)),
                    "affected_sessions_pct": row.get("sessionsWithMetricPercentage", 0),
                }

    return pages

# =========================
# JOB RUNNER
# =========================

def run():
    print(f" Clarity job started: {datetime.now(UTC).strftime('%H:%M:%S')}")

    now = datetime.now(UTC)
    from_ts = now - timedelta(hours=RANGE_HOURS)

    total = len(CLARITY_PROJECT_TOKENS)
    success = 0
    failed = 0

    print(f"📋 Processing {total} project(s)")

    for project_id, token in CLARITY_PROJECT_TOKENS.items():
        print(f"\n Project: {project_id}")
        start = time.time()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                API_URL,
                headers=headers,
                params={"numOfDays": 1, "dimension1": "URL"},
                timeout=30,
            )

            if response.status_code != 200:
                print(f" API failed: {response.status_code}")
                failed += 1
                continue

            pages = normalize_clarity(response.json())

            clarity_collection.insert_one({
                "project_id": project_id,
                "ranges": {
                    "24h": {
                        "from": from_ts,
                        "to": now,
                        "pages": pages,
                        "stats": {
                            "total_pages": len(pages),
                            "fetch_duration_ms": int((time.time() - start) * 1000),
                        },
                    }
                },
                "timestamps": {
                    "fetched_at": now,
                    "processed_at": datetime.now(UTC),
                },
            })

            print(f" Inserted {len(pages)} pages")
            success += 1

        except Exception as e:
            print(f" Error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(" CLARITY JOB SUMMARY")
    print("=" * 60)
    print(f" Success: {success}/{total}")
    print(f" Failed: {failed}/{total}")

if __name__ == "__main__":
    run()
