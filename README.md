# User Behaviour Analytics — Backend

FastAPI backend that collects user-behaviour analytics from **Umami** (self-hosted)
and **Microsoft Clarity**, normalizes the geo/traffic data, stores snapshots in
**MongoDB**, and serves them through a REST API.

## Features

- Umami integration with token-based auth (cached Bearer token)
- Microsoft Clarity export-data integration (multi-project support)
- Geo normalization for countries / regions / cities (`pycountry` + `geopy`)
- Scheduled background collection via APScheduler (24h, 7d, 30d, 90d, 1y ranges)
- MongoDB snapshot storage, served through FastAPI endpoints

## Project structure

```
app/
  main.py                 # FastAPI app entrypoint
  config.py               # env-based configuration
  database.py             # MongoDB client / collections
  schemas.py              # response models
  routes/analytics.py     # API endpoints
  services/
    umami_client.py       # Umami API client (login + metrics/stats/traffic)
    clarity_processor.py  # Clarity aggregation
    processor.py          # derived metrics
    normalizers/          # country / region / city normalization
  utils/range_mapper.py   # date-range helpers
jobs/
  fetch_all.py            # runs all collectors
  fetch_umami_job.py      # Umami collector (v1)
  fetch_umami_job_v2.py   # Umami collector (v2, multi-website)
  fetch_umami_job_v12.py  # Umami collector (v12)
  fetch_clarity_job.py    # Clarity collector
scheduler.py              # APScheduler runner
requirements.txt
```

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service status |
| GET | `/health` | Health check |
| GET | `/analytics/umami/websites` | List available Umami websites |
| GET | `/analytics/umami?website_id=` | Umami analytics snapshot |
| GET | `/analytics/clarity?project_id=` | Clarity analytics snapshot |
| GET | `/analytics/combined?website_id=&project_id=` | Merged Umami + Clarity data |

## Environment variables

Create a `.env` file in the project root (never committed):

```
MONGO_URI=...
DB_NAME=analytics
COLLECTION_NAME=umami_snapshots

UMAMI_BASE_URL=http://localhost:3000
UMAMI_USERNAME=...
UMAMI_PASSWORD=...
UMAMI_WEBSITE_ID=...

# Comma-separated project_id:token pairs
CLARITY_PROJECTS=projectId1:token1,projectId2:token2
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Run

```bash
# API
uvicorn app.main:app --reload

# Scheduled collectors
python scheduler.py
```
