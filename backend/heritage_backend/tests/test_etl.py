from datetime import date
from decimal import Decimal
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from django.conf import settings
from pymongo import MongoClient

from heritage_backend.core.management.commands.run_etl import refresh_projection
from mongo.client import active_collection


class FixtureCursor:
    def __init__(self, fail_on_bookings=False):
        self.fail_on_bookings = fail_on_bookings
        self.rows = []

    def execute(self, query):
        if "FROM heritage_site hs" in query:
            self.rows = [
                (
                    1,
                    "Test Heritage Site",
                    "Western Cape",
                    "Museum",
                    Decimal("25.00"),
                    True,
                    "Test description",
                )
            ]
        elif self.fail_on_bookings:
            raise RuntimeError("simulated source query failure")
        else:
            self.rows = [
                (
                    1,
                    1,
                    "Test Heritage Site",
                    "Western Cape",
                    2,
                    date(2025, 2, 1),
                    date(2025, 3, 1),
                    "Test Visitor",
                    "visitor@example.test",
                    False,
                    None,
                )
            ]

    def fetchall(self):
        return self.rows


@pytest.fixture
def isolated_mongo_db():
    parsed_uri = urlparse(settings.MONGO_URI)
    if parsed_uri.hostname not in {"localhost", "127.0.0.1", "::1", "mongo"}:
        pytest.fail("ETL tests require the isolated local MongoDB service.")

    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
    database_name = f"heritage_phase2_test_etl_{uuid4().hex}"
    database = client[database_name]
    try:
        yield database
    finally:
        client.drop_database(database_name)
        client.close()


def seed_previous_projection(database):
    sites = database["sites_previous"]
    sites.insert_one(
        {"site_id": 99, "name": "Previous site", "is_active": True}
    )
    sites.create_index("site_id", unique=True, name="previous_site_id_unique")
    bookings = database["bookings_previous"]
    bookings.insert_one(
        {"booking_id": 99, "is_cancelled": False}
    )
    bookings.create_index(
        "booking_id", unique=True, name="previous_booking_id_unique"
    )
    database["_etl_state"].insert_one({
        "_id": "active_projection",
        "generation": "previous",
        "collections": {
            "heritage_sites": "sites_previous",
            "bookings": "bookings_previous",
        },
    })


def test_refresh_publishes_both_collections_and_indexes(isolated_mongo_db):
    seed_previous_projection(isolated_mongo_db)

    counts = refresh_projection(FixtureCursor(), isolated_mongo_db)
    state = isolated_mongo_db["_etl_state"].find_one(
        {"_id": "active_projection"}
    )
    active_sites = active_collection("heritage_sites", isolated_mongo_db)
    active_bookings = active_collection("bookings", isolated_mongo_db)

    assert counts == (1, 1)
    assert state["generation"] != "previous"
    assert active_sites.find_one({"site_id": 1})["name"] == "Test Heritage Site"
    booking = active_bookings.find_one({"booking_id": 1})
    assert booking["is_cancelled"] is False
    assert booking["cancelled_at"] is None
    assert booking["booking_date"] == "2025-02-01"
    assert {
        index["name"] for index in active_sites.list_indexes()
    } >= {"site_id_unique", "active_province_site"}
    assert {
        index["name"] for index in active_bookings.list_indexes()
    } >= {
        "booking_id_unique",
        "booking_cancelled_site",
        "booking_cancelled_date",
    }
    assert active_collection(
        "heritage_sites", isolated_mongo_db
    ).find_one({"site_id": 99}) is None
    assert isolated_mongo_db["sites_previous"].find_one(
        {"site_id": 99}
    ) is not None


def test_failed_refresh_leaves_previous_projection_active(isolated_mongo_db):
    seed_previous_projection(isolated_mongo_db)

    with pytest.raises(RuntimeError, match="simulated source query failure"):
        refresh_projection(FixtureCursor(fail_on_bookings=True), isolated_mongo_db)

    state = isolated_mongo_db["_etl_state"].find_one(
        {"_id": "active_projection"}
    )
    assert state["generation"] == "previous"
    assert active_collection(
        "heritage_sites", isolated_mongo_db
    ).find_one({"site_id": 99}) is not None
    assert active_collection(
        "bookings", isolated_mongo_db
    ).find_one({"booking_id": 99}) is not None
    assert {
        index["name"]
        for index in active_collection(
            "heritage_sites", isolated_mongo_db
        ).list_indexes()
    } >= {"previous_site_id_unique"}
    assert {
        index["name"]
        for index in active_collection(
            "bookings", isolated_mongo_db
        ).list_indexes()
    } >= {"previous_booking_id_unique"}
    assert not any(
        name.startswith(("heritage_sites__", "bookings__"))
        for name in isolated_mongo_db.list_collection_names()
    )


def test_ambiguous_publication_failure_keeps_active_staging_collections(
    isolated_mongo_db
):
    seed_previous_projection(isolated_mongo_db)
    state_collection = isolated_mongo_db["_etl_state"]
    original_update = state_collection.update_one

    class PublicationAckFailure:
        def __getitem__(self, name):
            collection = isolated_mongo_db[name]
            if name != "_etl_state":
                return collection

            class StateCollection:
                def __getattr__(self, attribute):
                    return getattr(collection, attribute)

                def update_one(self, *args, **kwargs):
                    original_update(*args, **kwargs)
                    raise RuntimeError("simulated acknowledgement failure")

            return StateCollection()

    with pytest.raises(RuntimeError, match="simulated acknowledgement failure"):
        refresh_projection(FixtureCursor(), PublicationAckFailure())

    state = state_collection.find_one({"_id": "active_projection"})
    assert state["generation"] != "previous"
    assert active_collection(
        "heritage_sites", isolated_mongo_db
    ).find_one({"site_id": 1}) is not None
    assert active_collection(
        "bookings", isolated_mongo_db
    ).find_one({"booking_id": 1}) is not None
