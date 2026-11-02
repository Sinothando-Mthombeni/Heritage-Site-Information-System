"""
Refresh the MongoDB reporting projection from authoritative PostgreSQL data.

Usage:
    python manage.py run_etl
"""
import logging
import uuid

import psycopg2
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from pymongo import MongoClient


logger = logging.getLogger("heritage_backend")


def get_pg_connection():
    db = settings.DATABASES["default"]
    return psycopg2.connect(
        dbname=db["NAME"],
        user=db["USER"],
        password=db["PASSWORD"],
        host=db["HOST"],
        port=db["PORT"],
        **db.get("OPTIONS", {}),
    )


def get_mongo_db():
    client = MongoClient(settings.MONGO_URI)
    return client, client[settings.MONGO_DB_NAME]


def sync_heritage_sites(pg_cursor, collection):
    pg_cursor.execute("""
        SELECT
            hs.site_id,
            hs.name,
            p.name AS province,
            c.name AS category,
            hs.entry_fee,
            hs.is_active,
            hs.description
        FROM heritage_site hs
        JOIN province p ON p.province_id = hs.province_id
        JOIN category c ON c.category_id = hs.category_id
        ORDER BY hs.site_id;
    """)
    rows = pg_cursor.fetchall()
    if rows:
        collection.insert_many([
            {
                "site_id": row[0],
                "name": row[1],
                "province": row[2],
                "category": row[3],
                "entry_fee": float(row[4]) if row[4] is not None else None,
                "is_active": row[5],
                "description": row[6],
                "reviews": [],
            }
            for row in rows
        ])
    return len(rows)


def sync_bookings(pg_cursor, collection):
    pg_cursor.execute("""
        SELECT
            b.booking_id,
            b.site_id,
            hs.name AS site_name,
            p.name AS province,
            b.number_of_people AS visitors,
            b.booking_date,
            b.visit_date,
            v.full_name AS visitor_name,
            v.email AS visitor_email,
            b.is_cancelled,
            b.cancelled_at
        FROM booking b
        JOIN heritage_site hs ON hs.site_id = b.site_id
        JOIN province p ON p.province_id = hs.province_id
        JOIN visitor v ON v.visitor_id = b.visitor_id
        ORDER BY b.booking_id;
    """)
    rows = pg_cursor.fetchall()
    if rows:
        collection.insert_many([
            {
                "booking_id": row[0],
                "site_id": row[1],
                "site_name": row[2],
                "province": row[3],
                "visitors": row[4],
                "booking_date": row[5].isoformat() if row[5] else None,
                "visit_date": row[6].isoformat() if row[6] else None,
                "visitor_name": row[7],
                "visitor_email": row[8],
                "is_cancelled": row[9],
                "cancelled_at": row[10].isoformat() if row[10] else None,
            }
            for row in rows
        ])
    return len(rows)


def create_projection_indexes(sites, bookings):
    sites.create_index("site_id", unique=True, name="site_id_unique")
    sites.create_index(
        [("is_active", 1), ("province", 1), ("site_id", 1)],
        name="active_province_site",
    )
    bookings.create_index("booking_id", unique=True, name="booking_id_unique")
    bookings.create_index(
        [("is_cancelled", 1), ("site_id", 1)],
        name="booking_cancelled_site",
    )
    bookings.create_index(
        [("is_cancelled", 1), ("booking_date", 1)],
        name="booking_cancelled_date",
    )


def refresh_projection(pg_cursor, mongo_db):
    generation = uuid.uuid4().hex
    site_collection_name = f"heritage_sites__{generation}"
    booking_collection_name = f"bookings__{generation}"
    sites = mongo_db[site_collection_name]
    bookings = mongo_db[booking_collection_name]

    try:
        site_count = sync_heritage_sites(pg_cursor, sites)
        booking_count = sync_bookings(pg_cursor, bookings)
        create_projection_indexes(sites, bookings)
        mongo_db["_etl_state"].update_one(
            {"_id": "active_projection"},
            {
                "$set": {
                    "generation": generation,
                    "collections": {
                        "heritage_sites": site_collection_name,
                        "bookings": booking_collection_name,
                    },
                    "updated_at": timezone.now(),
                }
            },
            upsert=True,
        )
    except Exception:
        try:
            state = mongo_db["_etl_state"].find_one(
                {"_id": "active_projection"}
            )
        except Exception as cleanup_error:
            logger.error(
                "Could not inspect active ETL projection after refresh failure (%s)",
                type(cleanup_error).__name__,
            )
        else:
            active_collections = set(
                (state or {}).get("collections", {}).values()
            )
            for collection_name in (site_collection_name, booking_collection_name):
                if collection_name in active_collections:
                    continue
                try:
                    mongo_db.drop_collection(collection_name)
                except Exception as cleanup_error:
                    logger.error(
                        "Could not remove failed ETL staging collection (%s)",
                        type(cleanup_error).__name__,
                    )
        raise

    return site_count, booking_count


class Command(BaseCommand):
    help = "Refresh the MongoDB reporting projection from PostgreSQL."

    def handle(self, *args, **options):
        self.stdout.write("Starting ETL: PostgreSQL → MongoDB...")
        pg_conn = None
        mongo_client = None

        try:
            pg_conn = get_pg_connection()
            mongo_client, mongo_db = get_mongo_db()
            with pg_conn.cursor() as cursor:
                site_count, booking_count = refresh_projection(cursor, mongo_db)
        finally:
            if pg_conn is not None:
                pg_conn.close()
            if mongo_client is not None:
                mongo_client.close()

        self.stdout.write(self.style.SUCCESS(
            f"ETL complete — {site_count} site(s), {booking_count} booking(s) published."
        ))
