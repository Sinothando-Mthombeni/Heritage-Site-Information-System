from django.http import JsonResponse
from heritage_backend.services.reporting_service import (
    bookings_per_site,
    average_group_size,
    monthly_booking_stats,
    sites_with_provinces,
)

def bookings_per_site_view(request):
    data = list(bookings_per_site())
    return JsonResponse(data, safe=False)

def average_group_size_view(request):
    result = average_group_size()
    return JsonResponse({"average_group_size": result})

def monthly_booking_stats_view(request):
    data = list(monthly_booking_stats())
    return JsonResponse(data, safe=False)

def sites_with_provinces_view(request):
    data = list(sites_with_provinces().values("site_id", "name", "province__name", "entry_fee"))
    return JsonResponse(data, safe=False)