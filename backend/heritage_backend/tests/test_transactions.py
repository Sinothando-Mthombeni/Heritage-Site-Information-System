import pytest
from datetime import date
from services.booking_service import create_booking
from core.models import Booking

@pytest.mark.django_db
def test_successful_booking_creation():
    booking = create_booking(
        visitor_email="test@example.com",
        visitor_name="Test User",
        site_id=1,
        visit_date=date.today(),
        number_of_people=2
    )

    assert Booking.objects.count() == 1
    assert booking.number_of_people == 2


@pytest.mark.django_db
def test_booking_rollback_on_invalid_site():
    try:
        create_booking(
            visitor_email="fail@example.com",
            visitor_name="Fail User",
            site_id=9999,  # invalid
            visit_date=date.today(),
            number_of_people=2
        )
    except Exception:
        pass

    assert Booking.objects.count() == 0
