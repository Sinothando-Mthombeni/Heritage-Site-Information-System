from .client import active_collection


def get_all_sites(page=1, page_size=10, collection=None):
    collection = (
        collection if collection is not None else active_collection("heritage_sites")
    )
    offset = (page - 1) * page_size
    return list(
        collection.find(
            {"is_active": True},
            {"_id": 0}
        ).sort("site_id", 1).skip(offset).limit(page_size)
    )


def get_sites_by_province(province, collection=None):
    collection = (
        collection if collection is not None else active_collection("heritage_sites")
    )
    return list(
        collection.find(
            {"province": province, "is_active": True},
            {"_id": 0}
        ).sort("site_id", 1)
    )


def get_site_by_name(name, collection=None):
    collection = (
        collection if collection is not None else active_collection("heritage_sites")
    )
    documents = collection.find(
        {"name": name, "is_active": True},
        {"_id": 0},
    ).sort("site_id", 1).limit(1)
    return next(iter(documents), None)
