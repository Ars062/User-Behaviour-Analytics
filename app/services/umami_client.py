import requests
import time
from app.config import BASE_URL, UMAMI_USERNAME, UMAMI_PASSWORD

# ========================
# TOKEN CACHE
# ========================
TOKEN_CACHE = {
    "token": None,
    "expires_at": 0  # UNIX timestamp
}

def login():
    """Login to self-hosted Umami and cache token"""
    global TOKEN_CACHE
    
    # Reuse token if valid
    if TOKEN_CACHE["token"] and time.time() < TOKEN_CACHE["expires_at"]:
        return TOKEN_CACHE["token"]
    
    try:
        res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": UMAMI_USERNAME, "password": UMAMI_PASSWORD},
            timeout=15
        )
        res.raise_for_status()
        data = res.json()
        token = data.get("token")
        if not token:
            raise RuntimeError("Login failed: No token returned")
        
        # Cache token for 6 hours
        TOKEN_CACHE["token"] = token
        TOKEN_CACHE["expires_at"] = time.time() + 21600
        return token
    except Exception as e:
        raise RuntimeError(f"Login failed: {e}")

def get_headers():
    """Return Authorization header with Bearer token"""
    token = login()
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

# ========================
# FETCH FUNCTIONS
# ========================

def fetch_websites(include_teams=False, search=None, page=1, page_size=100):
    """Fetch all websites from Umami"""
    params = {
        "includeTeams": str(include_teams).lower(),
        "page": page,
        "pageSize": page_size
    }
    if search:
        params["search"] = search
    try:
        res = requests.get(
            f"{BASE_URL}/api/websites",
            headers=get_headers(),
            params=params,
            timeout=30
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f" Failed to fetch websites: {e}")
        raise

def fetch_metrics(website_id, metric_type, start_at, end_at, filters=None, **kwargs):
    """Fetch metrics with filters"""
    params = {"type": metric_type, "startAt": start_at, "endAt": end_at}
    
    # Handle filters parameter
    if filters:
        params.update(filters)
    
    # Handle additional kwargs
    params.update(kwargs)
    
    try:
        res = requests.get(
            f"{BASE_URL}/api/websites/{website_id}/metrics",
            headers=get_headers(),
            params=params,
            timeout=30
        )
        res.raise_for_status()
        payload = res.json()
        
        # Handle different response formats
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        elif isinstance(payload, list):
            return payload
        elif isinstance(payload, dict):
            return [payload]
        return []
    except Exception as e:
        print(f" Metric {metric_type} failed: {str(e)[:80]}")
        return []

def fetch_stats(website_id, start_at, end_at, filters=None, **kwargs):
    """Fetch stats with filters"""
    params = {"startAt": start_at, "endAt": end_at, "compare": "true"}
    
    
    if filters:
        params.update(filters)
     
    params.update(kwargs)
    
    try:
        res = requests.get(
            f"{BASE_URL}/api/websites/{website_id}/stats",
            headers=get_headers(),
            params=params,
            timeout=30
        )
        res.raise_for_status()
        data = res.json()
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f" Stats failed: {str(e)[:80]}")
        return {}

def fetch_traffic(website_id, unit, start_at, end_at, filters=None, **kwargs):
    """Fetch traffic data using /pageviews endpoint"""
    params = {"startAt": start_at, "endAt": end_at, "unit": unit, "timezone": "Asia/Kolkata"}
    
    # Handle filters parameter
    if filters:
        params.update(filters)
    
    # Handle additional kwargs
    params.update(kwargs)
    
    try:
        res = requests.get(
            f"{BASE_URL}/api/websites/{website_id}/pageviews",
            headers=get_headers(),
            params=params,
            timeout=30
        )
        if res.status_code == 200:
            data = res.json()
            print(f" Traffic API returned: {len(data.get('pageviews', []))} pageviews, {len(data.get('sessions', []))} sessions")
            return {"pageviews": data.get("pageviews", []), "sessions": data.get("sessions", [])}
        else:
            print(f" Traffic API failed: {res.status_code}")
            return {"pageviews": [], "sessions": []}
    except Exception as e:
        print(f" Traffic fetch error: {str(e)[:80]}")
        return {"pageviews": [], "sessions": []}