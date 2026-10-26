#    app/services/clarity_processor.py
# phase2
    # def compute_clarity_insights(aggregates):
    #     sessions = aggregates.get("sessions", 0)
    #     active_time = aggregates.get("total_active_time_sec", 0)
    #     total_time = aggregates.get("total_time_sec", 0)

    #     avg_active_time = (active_time / sessions) if sessions else 0
    #     engagement_ratio = (active_time / total_time) if total_time else 0
    #     idle_ratio = 1 - engagement_ratio if total_time else 0

    #     return {
    #         "avg_active_time_per_session": round(avg_active_time, 2),
    #         "engagement_ratio": round(engagement_ratio, 2),
    #         "idle_ratio": round(idle_ratio, 2)
    #     }
# Example Umami tracking snippet:
# <script defer src="https://cloud.umami.is/script.js" data-website-id="YOUR-WEBSITE-ID"></script>