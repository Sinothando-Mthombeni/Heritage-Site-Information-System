from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "heritage_phase3")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
