from django.urls import path
from .views_reports import (
    bookings_per_site_view,
    average_group_size_view,
    monthly_booking_stats_view,
    sites_with_provinces_view,
)

urlpatterns = [
    path("reports/bookings-per-site/", bookings_per_site_view),
    path("reports/average-group-size/", average_group_size_view),
    path("reports/monthly-stats/",      monthly_booking_stats_view),
    path("reports/sites/",              sites_with_provinces_view),
]