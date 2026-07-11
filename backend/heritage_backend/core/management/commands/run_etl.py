"""
heritage_backend/core/management/commands/run_etl.py

Runs the Postgres -> MongoDB ETL as a Django management command.
This means it uses Django's already-configured database settings
(DATABASES['default'] and MONGO_URI from settings.py), so it works
wherever Django works — locally, in Docker, or on any deployment host —
without needing to re-read .env independently.

Usage:
    python manage.py run_etl
"""
import psycopg2
from django.conf import settings
from django.core.management.base import BaseCommand
from pymongo import MongoClient


def get_pg_connection():
    db = settings.DATABASES["default"]
    return psycopg2.connect(
        dbname=db["NAME"],
        user=db["USER"],
        password=db["PASSWORD"],
        host=db["HOST"],
        port=db["PORT"],
    )


def get_mongo_db():
    client = MongoClient(settings.MONGO_URI)
    return client, client[settings.MONGO_DB_NAME]


def sync_heritage_sites(pg_cursor, mongo_db):
    pg_cursor.execute("""
        SELECT
            hs.site_id,
            hs.name,
            p.name  AS province,
            c.name  AS category,
            hs.entry_fee,
            hs.is_active,
            hs.description
        FROM heritage_site hs
        JOIN province p ON p.province_id = hs.province_id
        JOIN category c ON c.category_id = hs.category_id
        ORDER BY hs.site_id;
    """)
    rows = pg_cursor.fetchall()
    mongo_db.heritage_sites.delete_many({})
    if not rows:
        return 0
    mongo_db.heritage_sites.insert_many([
        {
            "site_id":     r[0],
            "name":        r[1],
            "province":    r[2],
            "category":    r[3],
            "entry_fee":   float(r[4]) if r[4] is not None else None,
            "is_active":   r[5],
            "description": r[6],
            "reviews":     [],
        }
        for r in rows
    ])
    return len(rows)


def sync_bookings(pg_cursor, mongo_db):
    pg_cursor.execute("""
        SELECT
            b.booking_id,
            b.site_id,
            hs.name            AS site_name,
            p.name             AS province,
            b.number_of_people AS visitors,
            b.booking_date,
            b.visit_date,
            v.full_name        AS visitor_name,
            v.email            AS visitor_email
        FROM booking b
        JOIN heritage_site hs ON hs.site_id  = b.site_id
        JOIN province p       ON p.province_id = hs.province_id
        JOIN visitor v        ON v.visitor_id  = b.visitor_id
        ORDER BY b.booking_id;
    """)
    rows = pg_cursor.fetchall()
    mongo_db.bookings.delete_many({})
    if not rows:
        return 0
    mongo_db.bookings.insert_many([
        {
            "booking_id":    r[0],
            "site_id":       r[1],
            "site_name":     r[2],
            "province":      r[3],
            "visitors":      r[4],
            "booking_date":  r[5].isoformat() if r[5] else None,
            "visit_date":    r[6].isoformat() if r[6] else None,
            "visitor_name":  r[7],
            "visitor_email": r[8],
        }
        for r in rows
    ])
    return len(rows)


class Command(BaseCommand):
    help = "Sync PostgreSQL transactional data into MongoDB for analytics."

    def handle(self, *args, **options):
        self.stdout.write("Starting ETL: PostgreSQL → MongoDB...")

        pg_conn     = get_pg_connection()
        mongo_client, mongo_db = get_mongo_db()

        try:
            with pg_conn.cursor() as cur:
                n_sites    = sync_heritage_sites(cur, mongo_db)
                n_bookings = sync_bookings(cur, mongo_db)
            pg_conn.commit()
        finally:
            pg_conn.close()
            mongo_client.close()

        self.stdout.write(self.style.SUCCESS(
            f"ETL complete — {n_sites} site(s), {n_bookings} booking(s) synced to MongoDB."
        ))
