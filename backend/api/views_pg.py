"""
api/views_pg.py

Transactional (PostgreSQL-backed) API views.
Input validation is handled by BookingSerializer before the service
layer is called, giving field-level error messages rather than
a bare try/except catching everything.
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django_ratelimit.decorators import ratelimit
from api.serializers import BookingSerializer
from api.decorators import api_error_handler
from heritage_backend.core.models import HeritageSite
from heritage_backend.services.booking_service import create_booking

logger = logging.getLogger('heritage_backend')


def ratelimit_error(request, exception):
    return JsonResponse({'status':'error','message':'Too many requests. Wait 1 minute.'},status=429)


@api_error_handler
@csrf_exempt
@require_POST
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def create_booking_view(request):
    if request.content_type != "application/json" and request.body:
        return JsonResponse(
            {"status": "error", "message": "Content-Type must be application/json."},
            status=415,
        )

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'status':'error','message':'Request body must be valid JSON.'},status=400)

    if not isinstance(data, dict):
        return JsonResponse(
            {"status": "error", "message": "Request body must be a JSON object."},
            status=400,
        )

    # Phase 3: use authenticated user's identity if logged in
    if hasattr(request,'user') and request.user.is_authenticated:
        data.setdefault('visitor_email', request.user.email)
        data.setdefault('visitor_name',  request.user.get_full_name() or request.user.username)

    serializer = BookingSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({'status':'error','errors':serializer.errors},status=400)

    vd = serializer.validated_data
    
    try:
        booking = create_booking(
            visitor_email=vd["visitor_email"],
            visitor_name=vd["visitor_name"],
            site_id=vd["site_id"],
            visit_date=vd["visit_date"],
            number_of_people=vd["number_of_people"])
    except HeritageSite.DoesNotExist:
        return JsonResponse(
            {
                "status": "error",
                "errors": {"site_id": ["The selected site is unavailable."]},
            },
            status=400,
        )

    logger.info("Booking #%s created", booking.booking_id)
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


@api_error_handler
@require_http_methods(["PATCH"])
def cancel_booking_view(request, booking_id):
    logger.warning("Booking cancellation is disabled pending Phase 3 ownership controls")
    return JsonResponse(
        {
            "status": "error",
            "message": "Booking cancellation is temporarily unavailable.",
        },
        status=503,
    )
