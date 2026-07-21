"""
api/views_reports.py

PostgreSQL-backed reporting endpoints. Each view delegates to a
service function and handles serialisation edge cases:
  - Decimal (entry_fee) → DjangoJSONEncoder
  - average_group_size() returns a dict aggregate → extract the value
  - monthly_booking_stats() returns raw SQL tuples → convert to dicts
"""
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse

from heritage_backend.services.reporting_service import (
    average_group_size,
    bookings_per_site,
    monthly_booking_stats,
    sites_with_provinces,
)


def bookings_per_site_view(request):
    """GET /api/reports/bookings-per-site/
    Returns a list of {heritage_site__name, total} ordered by most bookings.
    """
    data = list(bookings_per_site())
    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)


def average_group_size_view(request):
    """GET /api/reports/average-group-size/
    Returns {"average_group_size": <float>} across all bookings.
    average_group_size() returns Django's Avg aggregate dict,
    e.g. {"avg_people": Decimal("2.50")} or {"avg_people": None}.
    """
    result = average_group_size()
    raw = result.get("avg_people")
    value = round(float(raw), 2) if raw is not None else 0
    return JsonResponse({"average_group_size": value})


def monthly_booking_stats_view(request):
    """GET /api/reports/monthly-stats/
    Returns a list of {month, total_bookings} per calendar month.
    monthly_booking_stats() executes raw SQL and returns a list of
    tuples: [(datetime, int), ...] — these must be converted to dicts.
    """
    rows = monthly_booking_stats()
    data = [
        {"month": str(row[0])[:7], "total_bookings": row[1]}   # "YYYY-MM"
        for row in rows
    ]
    return JsonResponse(data, safe=False)


def sites_with_provinces_view(request):
    """GET /api/reports/sites/
    Returns all active heritage sites with their province name.
    Uses DjangoJSONEncoder to handle Decimal entry_fee values.
    """
    qs = sites_with_provinces().values(
        "site_id", "name", "province__name", "entry_fee", "is_active"
    )
    return JsonResponse(list(qs), safe=False, encoder=DjangoJSONEncoder)
