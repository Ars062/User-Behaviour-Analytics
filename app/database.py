# app/database.py

from pymongo import MongoClient
from app.config import MONGO_URI, DB_NAME, COLLECTION_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
clarity_collection = db["clarity_snapshots"]
# clarity_history_collection = db["clarity_history"]