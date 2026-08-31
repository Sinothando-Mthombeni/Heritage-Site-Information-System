from django.db import transaction, IntegrityError
from heritage_backend.core.models import Booking, Visitor, HeritageSite

@transaction.atomic
def create_booking(
    visitor_email,
    visitor_name,
    site_id,
    visit_date,
    number_of_people
):
    try:
        visitor, _ = Visitor.objects.get_or_create(
            email=visitor_email,
            defaults={"full_name": visitor_name}
        )

        site = HeritageSite.objects.get(
            site_id=site_id,
            is_active=True
        )

        booking = Booking.objects.create(
            visitor=visitor,
            heritage_site=site,
            visit_date=visit_date,
            number_of_people=number_of_people
        )

        return booking

    except IntegrityError as e:
        raise RuntimeError("Booking transaction failed") from e

def cancel_booking(booking_id):
    from django.utils import timezone
    from heritage_backend.core.models import Booking
    booking = Booking.objects.get(pk=booking_id)
    if booking.is_cancelled:
            raise ValueError('This booking is already cancelled.')
    if booking.visit_date < timezone.now().date():
        raise ValueError('Cannot cancel a booking for a past visit date.')
    booking.is_cancelled = True
    booking.cancelled_at = timezone.now()
    booking.save(update_fields=['is_cancelled','cancelled_at'])
    return booking
