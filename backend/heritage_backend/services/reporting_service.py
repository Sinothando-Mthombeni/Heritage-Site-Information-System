from django.db.models import Avg, Count
from django.db import connection
from heritage_backend.core.models import HeritageSite, Booking

def list_active_sites():
    return HeritageSite.objects.filter(is_active=True)

def sites_with_provinces():
    return HeritageSite.objects.filter(is_active=True).select_related("province")

def bookings_per_site():
    return (
        Booking.objects.filter(is_cancelled=False)
        .values(
            "heritage_site_id",
            "heritage_site__name",
            "heritage_site__province__name",
        )
        .annotate(total=Count("booking_id"))
        .order_by("-total", "heritage_site_id")
    )

def average_group_size():
    return Booking.objects.filter(is_cancelled=False).aggregate(
        avg_people=Avg("number_of_people")
    )

def monthly_booking_stats():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                DATE_TRUNC('month', booking_date) AS month,
                COUNT(*) AS total_bookings
            FROM booking
            WHERE is_cancelled = FALSE
            GROUP BY month
            ORDER BY month;
        """)
        return cursor.fetchall()
