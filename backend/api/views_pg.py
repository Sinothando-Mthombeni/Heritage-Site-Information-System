from django.http import JsonResponse
from services.booking_service import create_booking
from datetime import date

def create_booking_view(request):
    try:
        booking = create_booking(
            visitor_email=request.GET.get("email"),
            visitor_name=request.GET.get("name"),
            site_id=request.GET.get("site_id"),
            visit_date=date.fromisoformat(request.GET.get("visit_date")),
            number_of_people=int(request.GET.get("people"))
        )

        return JsonResponse({
            "status": "success",
            "booking_id": booking.booking_id
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=400)
