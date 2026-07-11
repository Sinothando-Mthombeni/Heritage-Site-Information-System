import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from heritage_backend.services.booking_service import create_booking
from datetime import date

@csrf_exempt
@require_POST
def create_booking_view(request):
    try:
        data = json.loads(request.body)
        booking = create_booking(
            visitor_email=data["visitor_email"],
            visitor_name=data["visitor_name"],
            site_id=data["site_id"],
            visit_date=data["visit_date"],
            number_of_people=data["number_of_people"],
        )
        return JsonResponse({
            "status": "success",
            "booking_id": booking.booking_id,
            "site": booking.heritage_site.name,
            "visit_date": str(booking.visit_date),
            "number_of_people": booking.number_of_people,
        }, status=201)
    except KeyError as e:
        return JsonResponse({"status": "error", "message": f"Missing field: {e}"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
