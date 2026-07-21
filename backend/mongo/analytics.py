from .client import db

heritage_sites = db.heritage_sites

def sites_per_province():
    pipeline = [
        {"$group": {"_id": "$province", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    return list(heritage_sites.aggregate(pipeline))

def average_entry_fee():
    pipeline = [
        {"$match": {"entry_fee": {"$ne": None}}},
        {"$group": {"_id": None, "avgFee": {"$avg": "$entry_fee"}}}
    ]
    result = list(heritage_sites.aggregate(pipeline))
    if not result:
        return 0
    avg = result[0].get("avgFee")
    return avg if avg is not None else 0
