from django.db.models import Count, Avg
from django.db import connection
from core.models import HeritageSite, Booking

def list_active_sites():
    return HeritageSite.objects.filter(is_active=True)

def sites_with_provinces():
    return HeritageSite.objects.select_related("province").all()

def bookings_per_site():
    return (
        Booking.objects
        .values("heritage_site__name")
        .annotate(total=Count("booking_id"))
        .order_by("-total")
    )

def average_group_size():
    return Booking.objects.aggregate(avg_people=Avg("number_of_people"))

def monthly_booking_stats():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                DATE_TRUNC('month', booking_date) AS month,
                COUNT(*) AS total_bookings
            FROM booking
            GROUP BY month
            ORDER BY month;
        """)
        return cursor.fetchall()
