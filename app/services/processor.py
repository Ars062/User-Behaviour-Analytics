# # app/services/processor.py

# def compute_extra_metrics(stats):
#     visits = stats.get("visits", 0)
#     bounces = stats.get("bounces", 0)
#     total_time = stats.get("totaltime", 0)

#     bounce_rate = (bounces / visits) * 100 if visits else 0
#     avg_duration = (total_time / visits) if visits else 0
#     # # Phase-2 (NEW)
#     # pages_per_session = (pageviews / visits) if visits else 0
#     # avg_time_per_page = (total_time / pageviews) if pageviews else 0
#     # engagement_proxy = (pageviews / visits) if visits else 0  # heuristic
#     return {
#         "bounce_rate": round(bounce_rate, 2),
#         "average_duration": round(avg_duration, 2)
#         # Phase-2 (NEW)
#         # "pages_per_session": round(pages_per_session, 2),
#         # "avg_time_per_page": round(avg_time_per_page, 2),
#         # "engagement_proxy": round(engagement_proxy, 2)
#     }


# def compute_per_item_metrics(data):
#     """
#     Convert raw metric data from Umami to structured items with computed metrics.
    
#     Input: [{"x": "value", "y": 100}, ...] or 
#            [{"x": "value", "visitors": 100, "visits": 110, "pageviews": 120, ...}, ...]
    
#     Output: [{"name": "value", "visitors": 100, "visits": 110, ...}, ...]
#     """
#     if not data:
#         return []
    
#     items = []
    
#     for item in data:
#         # Extract the name/identifier
#         name = item.get("x", "")
        
#         # Extract metrics - handle both formats
#         if "y" in item:
#             # Simple format: {"x": "value", "y": 100}
#             visitors = item.get("y", 0)
#             visits = item.get("y", 0)  # Same as visitors if not specified
#             pageviews = item.get("y", 0)  # Same as visitors if not specified
#         else:
#             # Expanded format: {"x": "value", "visitors": 100, "visits": 110, ...}
#             visitors = item.get("visitors", 0)
#             visits = item.get("visits", visitors)
#             pageviews = item.get("pageviews", visitors)
        
#         bounces = item.get("bounces", 0)
#         totaltime = item.get("totaltime", 0)
        
#         # Compute bounce rate and avg duration for this item
#         bounce_rate = (bounces / visits) * 100 if visits else 0
#         avg_duration = (totaltime / visits) if visits else 0
        
#         items.append({
#             "name": name,
#             "visitors": int(visitors),
#             "visits": int(visits),
#             "pageviews": int(pageviews),
#             "bounces": int(bounces),
#             "totaltime": int(totaltime),
#             "bounce_rate": round(bounce_rate, 2),
#             "average_duration": round(avg_duration, 2)
#         })
    
#     return items
# app/services/processor.py - FINAL CORRECTED VERSION

def compute_extra_metrics(stats):
    """Compute bounce rate and average duration from stats"""
    if not stats or not isinstance(stats, dict):
        return {"bounce_rate": 0, "average_duration": 0}
    
    try:
        pageviews = stats.get("pageviews", 0)
        bounces = stats.get("bounces", 0)
        totaltime = stats.get("totaltime", 0)
        visits = stats.get("visits", 0)
        
        # Calculate bounce rate
        bounce_rate = 0
        if visits and visits > 0:
            bounce_rate = round((bounces / visits) * 100, 2)
        
        # Calculate average duration
        average_duration = 0
        if visits and visits > 0:
            average_duration = round(totaltime / visits, 2)
        
        return {
            "bounce_rate": bounce_rate,
            "average_duration": average_duration
        }
    except Exception as e:
        print(f"⚠️  compute_extra_metrics error: {e}")
        return {"bounce_rate": 0, "average_duration": 0}

def compute_per_item_metrics(items):
    """Process individual metric items from Umami API"""
    if not items or not isinstance(items, list):
        return []
    
    processed = []
    
    for item in items:
        if not isinstance(item, dict):
            continue
        
        # Extract data based on known Umami response formats
        
        # For traffic data (pageviews/sessions) format: {"x": timestamp, "y": value}
        if "x" in item and "y" in item:
            processed.append({
                "name": str(item["x"]),
                "visitors": item["y"],
                "visits": item.get("visits", item["y"]),
                "pageviews": item.get("pageviews", item["y"]),
                "bounces": item.get("bounces", 0),
                "totaltime": item.get("totaltime", 0),
                "bounce_rate": 0,
                "average_duration": 0
            })
        
        # For URL/referrer metrics format: {"x": "url", "y": count, ...}
        elif "x" in item and "y" in item:
            visitors = item["y"]
            visits = item.get("visits", visitors)
            pageviews = item.get("pageviews", visitors)
            bounces = item.get("bounces", 0)
            totaltime = item.get("totaltime", 0)
            
            bounce_rate = round((bounces / visits * 100), 2) if visits > 0 else 0
            avg_duration = round((totaltime / visits), 2) if visits > 0 else 0
            
            processed.append({
                "name": item["x"],
                "visitors": visitors,
                "visits": visits,
                "pageviews": pageviews,
                "bounces": bounces,
                "totaltime": totaltime,
                "bounce_rate": bounce_rate,
                "average_duration": avg_duration
            })
        
        # For other metrics that might have different structure
        else:
            # Extract whatever fields are available
            name = item.get("name") or item.get("x") or item.get("url") or ""
            visitors = item.get("visitors") or item.get("y") or item.get("count") or 0
            visits = item.get("visits", visitors)
            pageviews = item.get("pageviews", visitors)
            bounces = item.get("bounces", 0)
            totaltime = item.get("totaltime", 0)
            
            bounce_rate = round((bounces / visits * 100), 2) if visits > 0 else 0
            avg_duration = round((totaltime / visits), 2) if visits > 0 else 0
            
            # For country data
            if "code" in item:
                processed.append({
                    "code": item["code"],
                    "name": item.get("name", name),
                    "iso3": item.get("iso3"),
                    "visitors": visitors
                })
            # For region data
            elif "region" in item:
                processed.append({
                    "region": item["region"],
                    "country": item.get("country"),
                    "lat": item.get("lat"),
                    "lon": item.get("lon"),
                    "visitors": visitors
                })
            # For all other metrics
            else:
                processed.append({
                    "name": name,
                    "visitors": visitors,
                    "visits": visits,
                    "pageviews": pageviews,
                    "bounces": bounces,
                    "totaltime": totaltime,
                    "bounce_rate": bounce_rate,
                    "average_duration": avg_duration
                })
    
    return processed