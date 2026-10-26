# jobs/fetch_umami_job_v2.py - FIXED VERSION
# python -m jobs.fetch_umami_job_v2

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, UTC
import time
from app.services.normalizers.country import normalize_countries
from app.services.normalizers.region import normalize_regions

from app.database import collection
from app.services.umami_client import fetch_stats, fetch_traffic, fetch_metrics, fetch_websites
from app.services.processor import compute_extra_metrics, compute_per_item_metrics
from app.utils.range_mapper import get_umami_range

print("UMAMI ANALYTICS FETCHER - FIXED VERSION")
print("=" * 80)

# ==================== CONFIGURATION ====================
MAX_WEBSITES = None      # None = ALL websites
TOP_PAGES_COUNT = 3      # Always get top 3 pages
DELAY_BETWEEN_CALLS = 0.2  # seconds for rate limiting
DELAY_BETWEEN_WEBSITES = 1  # seconds between websites

RANGES = ["24h", "7d", "30d", "90d", "1y"]
UNIT_MAP = {
    "24h": "hour",
    "7d": "day",
    "30d": "day",
    "90d": "month",
    "1y": "month"
}

# ==================== METRIC TYPES ====================
#  FIX: Use 'path' instead of 'url'
WHOLE_WEBSITE_METRIC_TYPES = [
    "path", "referrer", "country", "browser", "device", "os", "region", "city",
    "language", "screen", "entry", "exit", "channel"  
]

# ==================== PER-PAGE METRICS ====================
PER_PAGE_METRIC_TYPES = [
    "referrer", "country", "device", "browser", "os", "channel"
]

def fetch_with_delay(func, *args, **kwargs):
    """Fetch with delay for rate limiting"""
    result = func(*args, **kwargs)
    time.sleep(DELAY_BETWEEN_CALLS)
    return result

def fetch_single_website_analytics(website_id, website_info):
    """Fetch analytics for a single website across all ranges"""
    print(f"  Processing: {website_info.get('name', 'Unknown')}")
    
    all_ranges = {}
    total_api_calls = 0
    website_start_time = time.time()
    
    for range_key in RANGES:
        print(f"     Range: {range_key}")
        
        start_at, end_at = get_umami_range(range_key)
        unit = UNIT_MAP[range_key]
        
        try:
            # --- FETCH STATS ---
            stats = fetch_with_delay(fetch_stats, website_id, start_at, end_at)
            total_api_calls += 1
            extra = compute_extra_metrics(stats)
            
            if stats:
                print(f"        Stats: {stats.get('pageviews', 0)} pageviews, {stats.get('visitors', 0)} visitors")
            
            # --- FETCH TRAFFIC ---
            traffic_data = fetch_with_delay(fetch_traffic, website_id, unit, start_at, end_at)
            total_api_calls += 1
            
            pageviews_data = traffic_data.get("pageviews", [])
            sessions_data = traffic_data.get("sessions", [])
            
            # Build time series
            times = []
            pageviews = []
            sessions = []
            
            if pageviews_data:
                for item in pageviews_data:
                    if isinstance(item, dict) and "x" in item and "y" in item:
                        if item["x"] not in times:
                            times.append(item["x"])
            if sessions_data:
                for item in sessions_data:
                    if isinstance(item, dict) and "x" in item and "y" in item:
                        if item["x"] not in times:
                            times.append(item["x"])
            times.sort()
            
            pv_dict = {item["x"]: item["y"] for item in pageviews_data if isinstance(item, dict) and "x" in item and "y" in item}
            sess_dict = {item["x"]: item["y"] for item in sessions_data if isinstance(item, dict) and "x" in item and "y" in item}
            
            for t in times:
                pageviews.append(pv_dict.get(t, 0))
                sessions.append(sess_dict.get(t, 0))
            
            print(f"        Time points: {len(times)}")
            
            # --- FETCH EXPANDED METRICS ---
            expanded_metrics = {}
            for metric_type in WHOLE_WEBSITE_METRIC_TYPES:  
                try:
                    data = fetch_with_delay(fetch_metrics, website_id, metric_type, start_at, end_at)
                    total_api_calls += 1
                    
                    if data:
                        if metric_type == "country":
                            expanded_metrics[metric_type] = normalize_countries(data)
                        elif metric_type == "region":
                            expanded_metrics[metric_type] = normalize_regions(data)
                        elif metric_type == "city":
                            expanded_metrics[metric_type] = compute_per_item_metrics(data)
                        else:
                            expanded_metrics[metric_type] = compute_per_item_metrics(data)
                    else:
                        expanded_metrics[metric_type] = []
                        
                except Exception as e:
                    print(f"        {metric_type}: {str(e)[:50]}")
                    expanded_metrics[metric_type] = []
            
            # --- FETCH PER-PAGE BREAKDOWNS ---
            per_page_breakdowns = {}
            
            # Get top pages (using 'path' metric)
            try:
                pages = fetch_with_delay(fetch_metrics, website_id, "path", start_at, end_at)
                total_api_calls += 1
                
                if pages and len(pages) > 0:
                    print(f"        Found {len(pages)} pages")
                    top_pages = pages[:TOP_PAGES_COUNT]
                    
                    for page in top_pages:
                        page_path = page.get("x")
                        if not page_path:
                            continue
                        
                        print(f"         Processing page: {page_path}")
                        per_page_breakdowns[page_path] = {}
                        
                        # Fetch metrics for this specific page
                        for per_page_metric in PER_PAGE_METRIC_TYPES:
                            try:
                                
                                page_data = fetch_with_delay(
                                    fetch_metrics, 
                                    website_id, 
                                    per_page_metric, 
                                    start_at, 
                                    end_at,
                                    filters={"path": page_path}
                                )
                                total_api_calls += 1
                                per_page_breakdowns[page_path][per_page_metric] = page_data if page_data else []
                            except Exception as e:
                                print(f"            {per_page_metric}: {str(e)[:40]}")
                                per_page_breakdowns[page_path][per_page_metric] = []
                else:
                    print(f"        No page data available")
                    
            except Exception as e:
                print(f"        Failed to fetch pages: {str(e)[:50]}")
            
            # --- STORE RANGE DATA ---
            all_ranges[range_key] = {
                "start_at": start_at,
                "end_at": end_at,
                "stats": {**stats, "comparison": stats.get("comparison", {})} if stats else {},
                "bounce_rate": extra.get("bounce_rate", 0),
                "average_duration": extra.get("average_duration", 0),
                "traffic": {
                    "times": times,
                    "pageviews": pageviews,
                    "sessions": sessions
                },
                "expanded_metrics": expanded_metrics,
                "per_page_breakdowns": per_page_breakdowns
            }
            
        except Exception as e:
            print(f"      Range {range_key} failed: {str(e)[:80]}")
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
    print(f"      Completed: {total_api_calls} API calls in {website_time:.1f}s")
    
    return {
        "ranges": all_ranges,
        "fetch_stats": {
            "api_calls": total_api_calls,
            "duration_seconds": round(website_time, 2),
            "fetched_at": datetime.now(UTC)
        }
    }

def run():
    """Main function to fetch analytics for all websites"""
    print(f" Fetch started: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    total_start_time = time.time()
    
    # --- FETCH WEBSITES ---
    try:
        response = fetch_websites(include_teams=True, page_size=200)
        all_websites = response["data"]
        
        if MAX_WEBSITES is not None:
            all_websites = all_websites[:MAX_WEBSITES]
            print(f" TEST MODE: Limiting to {MAX_WEBSITES} websites")
        
        print(f" Found {len(all_websites)} website(s)")
        
        for i, website in enumerate(all_websites, 1):
            print(f"   {i}. {website.get('name', 'Unnamed')} ({website.get('domain', 'No domain')})")
        
    except Exception as e:
        print(f" CRITICAL: Failed to fetch websites: {e}")
        return 0
    
    # --- PROCESS EACH WEBSITE ---
    total_api_calls_all = 0
    successful_websites = 0
    failed_websites = 0
    websites_data = []
    
    print(f"\n{'='*80}")
    
    for idx, website in enumerate(all_websites, 1):
        website_id = website["id"]
        website_name = website.get("name", f"Website-{idx}")
        print(f" [{idx}/{len(all_websites)}] {website_name}")
        print(f"{'='*80}")
        
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
                "_stats": {
                    "fetch_time": datetime.now(UTC),
                    "api_calls": analytics_data["fetch_stats"]["api_calls"],
                    "duration_seconds": analytics_data["fetch_stats"]["duration_seconds"],
                    "version": "v2_fixed_final"
                }
            }
            
            websites_data.append(website_object)
            total_api_calls_all += analytics_data["fetch_stats"]["api_calls"]
            successful_websites += 1
            print(f"      Success\n")
            
        except Exception as e:
            print(f"     ❌ Failed: {str(e)[:100]}\n")
            failed_websites += 1
            websites_data.append({
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
                "ranges": {},
                "updated_at": datetime.now(UTC),
                "_stats": {
                    "fetch_time": datetime.now(UTC),
                    "api_calls": 0,
                    "duration_seconds": 0,
                    "version": "v2_fixed_final",
                    "error": str(e)[:200]
                }
            })
        
        # Delay between websites
        if idx < len(all_websites):
            time.sleep(DELAY_BETWEEN_WEBSITES)
    
    # --- SAVE TO MONGODB ---
    total_time = time.time() - total_start_time
    master_document = {
        "status": "partial_success" if failed_websites > 0 else "success",
        "status_code": 200 if successful_websites > 0 else 500,
        "version": "v2_fixed_final",
        "updated_at": datetime.now(UTC),
        "websites": websites_data,
        "global_stats": {
            "total_websites": len(all_websites),
            "successful_websites": successful_websites,
            "failed_websites": failed_websites,
            "total_api_calls": total_api_calls_all,
            "total_duration_seconds": round(total_time, 2),
            "fetch_time": datetime.now(UTC),
            "version": "v2_fixed_final"
        }
    }
    
    try:
        result = collection.insert_one(master_document)
        print(f"{'='*80}")
        print(f" MongoDB: Document saved (ID: {result.inserted_id})")
    except Exception as e:
        print(f" MongoDB storage failed: {e}")
        return 0
    
    # --- SUMMARY ---
    print(f"\n{'='*80}")
    print(f" FETCH COMPLETE!")
    print(f"{'='*80}")
    print(f"   Websites: {len(all_websites)} total")
    print(f"    Successful: {successful_websites}")
    print(f"    Failed: {failed_websites}")
    print(f"    Total API calls: {total_api_calls_all}")
    print(f"    Duration: {round(total_time/60, 2)} minutes")
    print(f"{'='*80}\n")
    
    return successful_websites

if __name__ == "__main__":
    run()