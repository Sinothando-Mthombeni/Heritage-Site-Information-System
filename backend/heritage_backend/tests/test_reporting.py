import pytest
from services.reporting_service import bookings_per_site

@pytest.mark.django_db
def test_bookings_per_site_returns_data():
    result = bookings_per_site()
    assert result is not None
