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
