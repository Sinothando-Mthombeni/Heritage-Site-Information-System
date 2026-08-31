from django.urls import path
from .views_reports import (
    bookings_per_site_view, average_group_size_view,
    monthly_booking_stats_view, sites_with_provinces_view,
    sites_by_province_count, sites_by_category_count, featured_sites_view,
    site_detail_view, export_bookings_csv,
)

urlpatterns = [
    path('reports/bookings-per-site/',  bookings_per_site_view),
    path('reports/average-group-size/', average_group_size_view),
    path('reports/monthly-stats/',      monthly_booking_stats_view),
    path('reports/sites/',              sites_with_provinces_view),
    path('reports/province-counts/',    sites_by_province_count),
    path('reports/category-counts/',    sites_by_category_count),
    path('reports/featured/',           featured_sites_view),
    path('reports/export/bookings/',    export_bookings_csv),
    path('sites/<int:site_id>/',        site_detail_view),

]
