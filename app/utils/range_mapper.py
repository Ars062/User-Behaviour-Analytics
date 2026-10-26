
# app/utils/range_mapper.py
import time

def get_umami_range(range_key: str):
    end = int(time.time() * 1000)

    ranges = {
        "24h": 24 * 60 * 60,
        "7d": 7 * 24 * 60 * 60,
        "30d": 30 * 24 * 60 * 60,
        "90d": 90 * 24 * 60 * 60,
        "1y": 365 * 24 * 60 * 60
    }

    if range_key not in ranges:
        raise ValueError("Invalid range")

    start = end - ranges[range_key] * 1000
    return start, end
