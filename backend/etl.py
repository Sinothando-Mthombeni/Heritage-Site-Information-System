import psycopg2
from pymongo import MongoClient

# ----------------------------
# PostgreSQL Connection
# ----------------------------
pg_conn = psycopg2.connect(
    dbname="heritage_phase2",
    user="postgres",
    password="password",
    host="localhost",
    port=5432
)

pg_cursor = pg_conn.cursor()

# ----------------------------
# MongoDB Connection
# ----------------------------
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["heritage_phase3"]

# ----------------------------
# Seed Heritage Sites
# ----------------------------
pg_cursor.execute("""
    SELECT site_id, name, province, category, ticket_price
    FROM heritage_sites;
""")

sites = pg_cursor.fetchall()

mongo_db.heritage_sites.delete_many({})

mongo_db.heritage_sites.insert_many([
    {
        "site_id": s[0],
        "name": s[1],
        "province": s[2],
        "category": s[3],
        "ticket_price": float(s[4]),
        "reviews": []
    }
    for s in sites
])

# ----------------------------
# Seed Bookings
# ----------------------------
pg_cursor.execute("""
    SELECT booking_id, site_id, site_name, province, visitors, booking_date
    FROM bookings;
""")

bookings = pg_cursor.fetchall()

mongo_db.bookings.delete_many({})

mongo_db.bookings.insert_many([
    {
        "booking_id": b[0],
        "site_id": b[1],
        "site_name": b[2],
        "province": b[3],
        "visitors": b[4],
        "booking_date": b[5]
    }
    for b in bookings
])

# ----------------------------
# Cleanup
# ----------------------------
pg_cursor.close()
pg_conn.close()
mongo_client.close()

print("MongoDB successfully seeded from PostgreSQL.")
