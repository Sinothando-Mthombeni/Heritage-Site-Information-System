"""
api/views_pg.py

Transactional (PostgreSQL-backed) API views.
Input validation is handled by BookingSerializer before the service
layer is called, giving field-level error messages rather than
a bare try/except catching everything.
"""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from api.serializers import BookingSerializer
from heritage_backend.services.booking_service import create_booking


@csrf_exempt
@require_POST
def create_booking_view(request):
    # Step 1 — parse JSON body
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"status": "error", "message": "Request body must be valid JSON."},
            status=400,
        )

    # Step 2 — validate fields with DRF serializer
    serializer = BookingSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(
            {"status": "error", "errors": serializer.errors},
            status=400,
        )

    # Step 3 — call the service layer
    vd = serializer.validated_data
    try:
        booking = create_booking(
            visitor_email=vd["visitor_email"],
            visitor_name=vd["visitor_name"],
            site_id=vd["site_id"],
            visit_date=vd["visit_date"],
            number_of_people=vd["number_of_people"],
        )
        return JsonResponse(
            {
                "status": "success",
                "booking_id": booking.booking_id,
                "site": booking.heritage_site.name,
                "visit_date": str(booking.visit_date),
                "number_of_people": booking.number_of_people,
            },
            status=201,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=400,
        )
