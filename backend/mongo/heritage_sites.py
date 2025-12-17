from .client import db

heritage_sites_collection = db.heritage_sites

def get_all_sites():
    return list(
        heritage_sites_collection.find(
            {},
            {"_id": 0}
        )
    )

def get_sites_by_province(province):
    return list(
        heritage_sites_collection.find(
            {"province": province},
            {"_id": 0}
        )
    )

def get_site_by_name(name):
    return heritage_sites_collection.find_one(
        {"name": name},
        {"_id": 0}
    )
