# app/config.py
import os
from dotenv import load_dotenv

# Load .env variables
# load_dotenv()
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


# ========================
# UMAMI API CONFIG
# ========================
# UMAMI_API_KEY = os.getenv("UMAMI_API_KEY")
# BASE_URL = os.getenv("UMAMI_BASE_URL", "https://api.umami.is/v1")
#self hosted umami 
UMAMI_USERNAME = os.getenv("UMAMI_USERNAME")
UMAMI_PASSWORD = os.getenv("UMAMI_PASSWORD")
BASE_URL = os.getenv("UMAMI_BASE_URL", "http://localhost:3000")  
# ========================
# DATABASE CONFIG
# ========================
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "analytics")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "umami_snapshots")
if not MONGO_URI:
    raise RuntimeError(" MONGO_URI not found in .env")
# ========================
raw = os.getenv("CLARITY_PROJECTS", "")

CLARITY_PROJECT_TOKENS = {}
for pair in raw.split(","):
    if not pair.strip():
        continue
    project_id, token = pair.split(":", 1)
    CLARITY_PROJECT_TOKENS[project_id.strip()] = token.strip()

if not CLARITY_PROJECT_TOKENS:
    raise RuntimeError(" CLARITY_PROJECTS missing or empty in .env")
# HEADERS
# ========================
# HEADERS = {
#     "x-umami-api-key": UMAMI_API_KEY,
#     "Accept": "application/json"
# }

# ========================
# SAFETY CHECK (optional but recommended)
# ========================
# if not UMAMI_API_KEY:
#     raise RuntimeError("❌ UMAMI_API_KEY not found in .env")

if not UMAMI_USERNAME:
    raise RuntimeError(" UMAMI_USERNAME not found in .env")
if not UMAMI_PASSWORD:
    raise RuntimeError(" UMAMI_PASSWORD not found in .env")
if not MONGO_URI:
    raise RuntimeError(" MONGO_URI not found in .env")
# if not CLARITY_TOKEN:
#     raise RuntimeError("❌ CLARITY_TOKEN not found in .env")
# if not PROJECT_IDS:
#     raise RuntimeError("❌ PROJECT_IDS not found in .env")
# print("ENV PROJECT_IDS =", os.environ.get("PROJECT_IDS"))
