# jobs/fetch_umami_job_v2.py
# python -m jobs.fetch_umami_job_v2

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, UTC
import time
from app.services.normalizers.country import normalize_countries
from app.services.normalizers.region import normalize_regions
from app.services.processor import compute_per_item_metrics, compute_extra_metrics
from app.database import collection
from app.services.umami_client import fetch_stats, fetch_traffic, fetch_metrics, fetch_websites
from app.utils.range_mapper import get_umami_range

print("UMAMI ANALYTICS FETCHER - UPDATED METRICS")
print("=" * 80)

# ---------------- CONFIG ----------------
MAX_WEBSITES = None
TOP_PAGES_COUNT = 3
DELAY_BETWEEN_CALLS = 0.2
DELAY_BETWEEN_WEBSITES = 1

RANGES = ["24h", "7d", "30d", "90d", "1y"]
UNIT_MAP = {"24h": "hour", "7d": "day", "30d": "day", "90d": "month", "1y": "month"}

SAFE_GLOBAL_METRICS = [
    "referrer", "browser", "device", "os", "language", "screen", "entry", "exit", "channel"
]
GEO_ROOT_METRICS = ["country"]
PER_PAGE_METRIC_TYPES = ["referrer", "country", "device", "browser", "screen", "channel"]

# ---------------- HELPERS ----------------
def fetch_with_delay(func, *args, **kwargs):
    result = func(*args, **kwargs)
    time.sleep(DELAY_BETWEEN_CALLS)
    return result

# ---------------- FETCH SINGLE WEBSITE ----------------
def fetch_single_website_analytics(website_id, website_info):
    print(f"  Processing: {website_info.get('name', 'Unknown')}")
    all_ranges = {}
    total_api_calls = 0
    website_start_time = time.time()

    for range_key in RANGES:
        print(f"     Range: {range_key}")
        start_at, end_at = get_umami_range(range_key)
        unit = UNIT_MAP[range_key]

        try:
            # Stats
            stats = fetch_with_delay(fetch_stats, website_id, start_at, end_at)
            total_api_calls += 1
            extra = compute_extra_metrics(stats)
            if stats:
                print(f"       Stats: {stats.get('pageviews', 0)} pageviews, {stats.get('visitors', 0)} visitors")

            # Traffic
            traffic_data = fetch_with_delay(fetch_traffic, website_id, unit, start_at, end_at)
            total_api_calls += 1
            pageviews_data = traffic_data.get("pageviews", [])
            sessions_data = traffic_data.get("sessions", [])
            print(f"    Traffic: {len(pageviews_data)} pageview points, {len(sessions_data)} session points")

            # Time series
            times = sorted({item["x"] for item in pageviews_data + sessions_data if isinstance(item, dict) and "x" in item})
            pv_dict = {item["x"]: item["y"] for item in pageviews_data if "x" in item and "y" in item}
            sess_dict = {item["x"]: item["y"] for item in sessions_data if "x" in item and "y" in item}
            pageviews = [pv_dict.get(t, 0) for t in times]
            sessions = [sess_dict.get(t, 0) for t in times]
            print(f"      📈 Time points: {len(times)}")

            # ---------------- GLOBAL METRICS ----------------
            expanded_metrics = {}
            for metric in SAFE_GLOBAL_METRICS:
                try:
                    data = fetch_with_delay(fetch_metrics, website_id, metric, start_at, end_at)
                    total_api_calls += 1
                    expanded_metrics[metric] = compute_per_item_metrics(data) if data else []
                except Exception as e:
                    print(f"       {metric} failed: {str(e)[:50]}")
                    expanded_metrics[metric] = []

            # ---------------- GEO METRICS ----------------
            expanded_metrics["country"] = []
            expanded_metrics["region"] = {}
            expanded_metrics["city"] = {}
            try:
                countries = fetch_with_delay(fetch_metrics, website_id, "country", start_at, end_at) or []
                total_api_calls += 1
                expanded_metrics["country"] = normalize_countries(countries)
                for c in countries:
                    country_code = c.get("x")
                    if not country_code:
                        continue
                    regions = fetch_with_delay(fetch_metrics, website_id, "region", start_at, end_at, filters={"country": country_code}) or []
                    total_api_calls += 1
                    expanded_metrics["region"][country_code] = normalize_regions(regions)
                    for r in regions:
                        region_code = r.get("x")
                        if not region_code:
                            continue
                        cities = fetch_with_delay(fetch_metrics, website_id, "city", start_at, end_at, filters={"country": country_code, "region": region_code}) or []
                        total_api_calls += 1
                        expanded_metrics["city"][f"{country_code}-{region_code}"] = cities
            except Exception as e:
                print(f"       GEO METRICS ERROR: {str(e)[:50]}")

            # ---------------- PAGE METRICS ----------------
            per_page_breakdowns = {}
            try:
                pages = fetch_with_delay(fetch_metrics, website_id, "url", start_at, end_at) or []
                total_api_calls += 1
                top_pages = pages[:TOP_PAGES_COUNT]
                for page in top_pages:
                    path = page.get("x")
                    if not path:
                        continue
                    per_page_breakdowns[path] = {}
                    for metric in PER_PAGE_METRIC_TYPES:
                        try:
                            data = fetch_with_delay(fetch_metrics, website_id, metric, start_at, end_at, filters={"url": path}) or []
                            total_api_calls += 1
                            per_page_breakdowns[path][metric] = data
                        except:
                            per_page_breakdowns[path][metric] = []
            except Exception as e:
                print(f"       PAGE METRICS ERROR: {str(e)[:50]}")

            # ---------------- ASSEMBLE RANGE ----------------
            all_ranges[range_key] = {
                "start_at": start_at,
                "end_at": end_at,
                "stats": {**stats, "comparison": stats.get("comparison", {})} if stats else {},
                "bounce_rate": extra.get("bounce_rate", 0),
                "average_duration": extra.get("average_duration", 0),
                "traffic": {"times": times, "pageviews": pageviews, "sessions": sessions},
                "expanded_metrics": expanded_metrics,
                "per_page_breakdowns": per_page_breakdowns
            }

        except Exception as e:
            print(f"     Range {range_key} failed: {str(e)[:80]}")
            all_ranges[range_key] = {
                "start_at": start_at,
                "end_at": end_at,
                "stats": {},
                "bounce_rate": 0,
                "average_duration": 0,
                "traffic": {"times": [], "pageviews": [], "sessions": []},
                "expanded_metrics": {},
                "per_page_breakdowns": {}
            }

    website_time = time.time() - website_start_time
    print(f"     API Calls: total={total_api_calls}, completed in {website_time:.1f}s")
    return {
        "ranges": all_ranges,
        "fetch_stats": {
            "api_calls": total_api_calls,
            "duration_seconds": round(website_time, 2),
            "fetched_at": datetime.now(UTC)
        }
    }

# ---------------- RUN ----------------
def run():
    print(f" Fetch started: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    total_start_time = time.time()

    try:
        response = fetch_websites(include_teams=True, page_size=200)
        all_websites = response["data"]
        if MAX_WEBSITES:
            all_websites = all_websites[:MAX_WEBSITES]
        print(f" Found {len(all_websites)} website(s)")
    except Exception as e:
        print(f" CRITICAL: Failed to fetch websites: {e}")
        return 0

    total_api_calls_all = 0
    successful_websites = 0
    failed_websites = 0
    websites_data = []

    for idx, website in enumerate(all_websites, 1):
        website_id = website["id"]
        website_name = website.get("name", f"Website-{idx}")
        print(f" Processing: {website_name}")
        try:
            analytics_data = fetch_single_website_analytics(website_id, website)
            website_object = {
                "website_info": {
                    "id": website_id,
                    "name": website.get("name"),
                    "domain": website.get("domain"),
                    "owner": website.get("user", {}).get("username"),
                    "created_at": website.get("createdAt"),
                    "updated_at": website.get("updatedAt"),
                    "share_id": website.get("shareId"),
                    "team_id": website.get("teamId")
                },
                "ranges": analytics_data["ranges"],
                "updated_at": datetime.now(UTC),
                "_stats": analytics_data["fetch_stats"]
            }
            websites_data.append(website_object)
            total_api_calls_all += analytics_data["fetch_stats"]["api_calls"]
            successful_websites += 1
        except Exception as e:
            failed_websites += 1
            websites_data.append({
                "website_info": {"id": website_id, "name": website.get("name")},
                "ranges": {},
                "updated_at": datetime.now(UTC),
                "_stats": {"api_calls": 0, "duration_seconds": 0, "error": str(e)[:200]}
            })

        if idx < len(all_websites):
            time.sleep(DELAY_BETWEEN_WEBSITES)

    # ---------------- INSERT NEW DOCUMENT ----------------
    total_time = time.time() - total_start_time
    master_document = {
        "status": "partial_success" if failed_websites > 0 else "success",
        "status_code": 200 if successful_websites > 0 else 500,
        "version": "v2_with_websites",
        "updated_at": datetime.now(UTC),
        "websites": websites_data,
        "global_stats": {
            "total_websites": len(all_websites),
            "successful_websites": successful_websites,
            "failed_websites": failed_websites,
            "total_api_calls": total_api_calls_all,
            "total_duration_seconds": round(total_time, 2),
            "fetch_time": datetime.now(UTC),
            "version": "v2_with_websites"
        }
    }

    try:
        result = collection.insert_one(master_document)
        print(f" MongoDB: INSERTED new document (ID: {result.inserted_id})")
    except Exception as e:
        print(f" MongoDB storage failed: {e}")
        return 0

    print(f" FETCH COMPLETE! Total websites: {len(all_websites)}, Successful: {successful_websites}, Failed: {failed_websites}")
    print(f"  Total time: {round(total_time/60, 2)} minutes")
    return successful_websites

if __name__ == "__main__":
    run()
