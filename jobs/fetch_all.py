# jobs/fetch_all.py - ROBUST VERSION
from jobs.fetch_umami_job_v2 import run as run_umami
from jobs.fetch_clarity_job import run as run_clarity
import traceback
from datetime import datetime, UTC
import time

def run_all():
    """Run all fetch jobs with error handling"""
    print(f"\n{'='*80}")
    print(f"🚀 FETCH ALL STARTED: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}")
    print('=' * 80)
    
    results = []
    start_time = time.time()
    
    # ========== UMANI FETCH ==========
    print("\n1️⃣  STARTING UMANI FETCH...")
    try:
        websites_processed = run_umami()
        results.append({
            "job": "umami",
            "status": "success",
            "details": f"Processed {websites_processed} websites",
            "time": datetime.now(UTC)
        })
        print(f"✅ UMANI: Success ({websites_processed} websites)")
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)[:100]}"
        results.append({
            "job": "umami", 
            "status": "failed",
            "error": error_msg,
            "time": datetime.now(UTC)
        })
        print(f"❌ UMANI: Failed - {error_msg}")
        traceback.print_exc()
    
    # ========== CLARITY FETCH ==========
    print("\n2️⃣  STARTING CLARITY FETCH...")
    try:
        projects_processed = run_clarity()
        results.append({
            "job": "clarity",
            "status": "success", 
            "details": f"Processed {projects_processed} projects",
            "time": datetime.now(UTC)
        })
        print(f"✅ CLARITY: Success ({projects_processed} projects)")
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)[:100]}"
        results.append({
            "job": "clarity",
            "status": "failed",
            "error": error_msg,
            "time": datetime.now(UTC)
        })
        print(f"❌ CLARITY: Failed - {error_msg}")
        traceback.print_exc()
    
    # ========== SUMMARY ==========
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r["status"] == "success")
    
    print(f"\n{'='*80}")
    print("📊 FINAL SUMMARY:")
    print('=' * 80)
    
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"  {status_icon} {result['job'].upper():10}: {result['status'].upper()}")
        if result["status"] == "success":
            print(f"       Details: {result.get('details', 'N/A')}")
        else:
            print(f"       Error: {result.get('error', 'N/A')}")
    
    print(f"\n⏱️  Total time: {total_time:.2f} seconds")
    print(f"📈 Success rate: {success_count}/{len(results)} jobs")
    print(f"🕒 Completed at: {datetime.now(UTC).strftime('%H:%M:%S')}")
    print('=' * 80)
    
    # Return summary for monitoring
    return {
        "timestamp": datetime.now(UTC),
        "results": results,
        "success_rate": f"{success_count}/{len(results)}",
        "total_seconds": round(total_time, 2)
    }

if __name__ == "__main__":
    run_all()