"""
api/views_pg.py

Transactional (PostgreSQL-backed) API views.
Input validation is handled by BookingSerializer before the service
layer is called, giving field-level error messages rather than
a bare try/except catching everything.
"""
import json, logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from api.serializers import BookingSerializer
from heritage_backend.services.booking_service import create_booking

logger = logging.getLogger('heritage_backend')

def ratelimit_error(request, exception):
    return JsonResponse({'status':'error','message':'Too many requests. Wait 1 minute.'},status=429)



@csrf_exempt
@require_POST
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def create_booking_view(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'status':'error','message':'Request body must be valid JSON.'},status=400)

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
        logger.info(f'Booking #{booking.booking_id} created')
        
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
        logger.error(f'Booking failed: {e}')
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=400,
        )
# Phase 2 — cancel view added below
def cancel_booking_view(request, booking_id):
    from heritage_backend.services.booking_service import cancel_booking
    from heritage_backend.core.models import Booking
    if request.method != 'PATCH':
        return JsonResponse({'status':'error','message':'Method not allowed'},status=405)
    try:
        booking = cancel_booking(booking_id)
        return JsonResponse({'status':'cancelled','booking_id':booking.booking_id})
    except Booking.DoesNotExist:
        return JsonResponse({'status':'error','message':'Booking not found'},status=404)
    except ValueError as e:
        return JsonResponse({'status':'error','message':str(e)},status=400)
    except Exception as e:
        return JsonResponse({'status':'error','message':str(e)},status=400)
