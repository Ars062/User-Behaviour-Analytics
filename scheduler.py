from apscheduler.schedulers.blocking import BlockingScheduler
from jobs.fetch_all import run_all
from datetime import datetime, UTC

scheduler = BlockingScheduler(timezone="UTC")

scheduler.add_job(
    run_all,
    trigger="interval", 
    seconds=90,     # 🔥 TEST MODE hours=6
    id="fetch_all_jobs",
    replace_existing=True,
    max_instances=2, #,3
    coalesce=True
)

print("🧪 Test scheduler started (runs every 30 seconds)")
print("🕒 Current time:", datetime.now(UTC).strftime("%H:%M:%S"))
scheduler.start()
# python scheduler.py
