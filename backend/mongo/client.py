from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "heritage_phase3")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


def active_collection(name, database=None):
    database = database if database is not None else db
    state = database["_etl_state"].find_one({"_id": "active_projection"})
    collection_name = state.get("collections", {}).get(name) if state else None
    return database[collection_name or name]
