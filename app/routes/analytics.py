# app/routes/analytics.py

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, UTC
from app.database import collection, clarity_collection

router = APIRouter()

# ===================================================
# Helpers
# ===================================================

def get_latest_umami_snapshot():
    """
    Returns the most recent Umami fetch document
    (one document per cron run)
    """
    return collection.find_one({}, sort=[("updated_at", -1)])


def get_latest_clarity_snapshot(project_id: str):
    """
    Returns the latest Clarity snapshot for a project
    """
    return clarity_collection.find_one(
        {"project_id": project_id},
        sort=[("timestamps.fetched_at", -1)]
    )

# ===================================================
# GET Umami Analytics (Latest Snapshot, One Website)
# ===================================================

@router.get("/analytics/umami")
def get_umami_analytics(
    website_id: str = Query(...),
    range: str = Query("24h", pattern="^(24h|7d|30d|90d|1y)$")
):
    snapshot = get_latest_umami_snapshot()

    if not snapshot:
        raise HTTPException(status_code=404, detail="No Umami data available")

    website = next(
        (
            w for w in snapshot.get("websites", [])
            if w.get("website_info", {}).get("id") == website_id
        ),
        None
    )

    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    range_data = website.get("ranges", {}).get(range)
    if not range_data:
        raise HTTPException(status_code=404, detail=f"No data for range {range}")

    return {
        "website_info": website.get("website_info"),
        "range": range,
        "snapshot_at": snapshot.get("updated_at"),
        "from": range_data.get("start_at"),
        "to": range_data.get("end_at"),
        "stats": range_data.get("stats", {}),
        "bounce_rate": range_data.get("bounce_rate", 0),
        "average_duration": range_data.get("average_duration", 0),
        "traffic": range_data.get("traffic", {}),
        "metrics": range_data.get("expanded_metrics", {}),
        "per_page": range_data.get("per_page_breakdowns", {})
    }

# ===================================================
# GET Umami Websites List (Latest Snapshot)
# ===================================================

@router.get("/analytics/umami/websites")
def get_umami_websites():
    snapshot = get_latest_umami_snapshot()

    if not snapshot:
        return {"total": 0, "websites": []}

    websites = [
        {
            "id": w["website_info"]["id"],
            "name": w["website_info"]["name"],
            "domain": w["website_info"]["domain"],
            "owner": w["website_info"].get("owner"),
            "updated_at": w.get("updated_at"),
        }
        for w in snapshot.get("websites", [])
    ]

    return {
        "snapshot_at": snapshot.get("updated_at"),
        "total": len(websites),
        "websites": websites
    }

# ===================================================
# GET Clarity Analytics (Latest 24h Snapshot)
# ===================================================

@router.get("/analytics/clarity")
def get_clarity_analytics(
    project_id: str = Query(...),
    range: str = Query("24h", pattern="^(24h)$")
):
    doc = get_latest_clarity_snapshot(project_id)

    if not doc:
        raise HTTPException(status_code=404, detail="No Clarity data available")

    range_data = doc.get("ranges", {}).get("24h")
    if not range_data:
        raise HTTPException(status_code=404, detail="24h range missing")

    pages = []
    total_sessions = 0
    total_users = 0

    for url, page in range_data.get("pages", {}).items():
        traffic = page.get("traffic", {})
        total_sessions += traffic.get("sessions", 0)
        total_users += traffic.get("users", 0)

        pages.append({
            "url": url,
            "traffic": traffic,
            "engagement": page.get("engagement", {}),
            "behavioral_insights": page.get("behavioral_insights", {})
        })

    return {
        "project_id": project_id,
        "range": "24h",
        "from": range_data.get("from"),
        "to": range_data.get("to"),
        "snapshot_at": doc["timestamps"]["fetched_at"],
        "stats": {
            "total_pages": len(pages),
            "total_sessions": total_sessions,
            "total_users": total_users
        },
        "pages": pages
    }

# ===================================================
# GET Combined Analytics (Latest Only, No Comparison)
# ===================================================

@router.get("/analytics/combined")
def get_combined_analytics(
    website_id: str = Query(...),
    project_id: str = Query(...),
    range: str = Query("24h", pattern="^(24h|7d|30d|90d|1y)$")
):
    umami_snapshot = get_latest_umami_snapshot()
    clarity_snapshot = get_latest_clarity_snapshot(project_id)

    umami_data = {}
    if umami_snapshot:
        for w in umami_snapshot.get("websites", []):
            if w.get("website_info", {}).get("id") == website_id:
                umami_data = w.get("ranges", {}).get(range, {})
                break

    clarity_data = {}
    if clarity_snapshot:
        clarity_data = clarity_snapshot.get("ranges", {}).get("24h", {})

    return {
        "timestamp": datetime.now(UTC),
        "range": range,
        "umami": umami_data,
        "clarity": clarity_data
    }

# ===================================================
# Health Check
# ===================================================

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC),
        "mongo_connected": True,
        "latest_umami": bool(get_latest_umami_snapshot()),
        "latest_clarity": bool(clarity_collection.find_one())
    }
