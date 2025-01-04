from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["tlc-shift"]

trips_collection = db["trips"]
