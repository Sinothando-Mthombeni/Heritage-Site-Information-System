from .client import active_collection



def sites_per_province(collection=None):
    collection = collection if collection is not None else active_collection("heritage_sites")
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$province", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}}
    ]
    return list(collection.aggregate(pipeline))


def average_entry_fee(collection=None):
    collection = collection if collection is not None else active_collection("heritage_sites")
    pipeline = [
        {"$match": {"is_active": True, "entry_fee": {"$ne": None}}},
        {"$group": {"_id": None, "avgFee": {"$avg": "$entry_fee"}}}
    ]
    result = list(collection.aggregate(pipeline))
    if not result:
        return 0
    avg = result[0].get("avgFee")
    return avg if avg is not None else 0


def bookings_per_site(collection=None):
    collection = collection if collection is not None else active_collection("bookings")
    pipeline = [
        {"$match": {"is_cancelled": {"$ne": True}}},
        {
            "$group": {
                "_id": "$site_id",
                "heritage_site__name": {"$first": "$site_name"},
                "heritage_site__province__name": {"$first": "$province"},
                "total": {"$sum": 1},
            }
        },
        {"$sort": {"total": -1, "_id": 1}},
        {
            "$project": {
                "_id": 0,
                "heritage_site_id": "$_id",
                "heritage_site__name": 1,
                "heritage_site__province__name": 1,
                "total": 1,
            }
        },
    ]
    return list(collection.aggregate(pipeline))


def average_group_size(collection=None):
    collection = collection if collection is not None else active_collection("bookings")
    result = list(
        collection.aggregate(
            [
                {"$match": {"is_cancelled": {"$ne": True}}},
                {"$group": {"_id": None, "average": {"$avg": "$visitors"}}},
            ]
        )
    )
    average = result[0]["average"] if result else None
    return round(float(average), 2) if average is not None else 0


def monthly_booking_stats(collection=None):
    collection = collection if collection is not None else active_collection("bookings")
    pipeline = [
        {"$match": {
            "is_cancelled": {"$ne": True},
            "booking_date": {"$type": "string", "$regex": r"^\d{4}-\d{2}-\d{2}$"},
        }},
        {
            "$group": {
                "_id": {"$substr": ["$booking_date", 0, 7]},
                "total_bookings": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
        {"$project": {"_id": 0, "month": "$_id", "total_bookings": 1}},
    ]
    return list(collection.aggregate(pipeline))
