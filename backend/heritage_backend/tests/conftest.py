import pytest

from heritage_backend.core.models import Category, HeritageSite, Province


@pytest.fixture
def active_site(db):
    """A single active HeritageSite (site_id=1) for booking-related tests."""
    province = Province.objects.create(name="Mpumalanga")
    category = Category.objects.create(name="Museum")
    return HeritageSite.objects.create(
        name="Test Heritage Site",
        description="A site used for automated tests.",
        entry_fee=50.00,
        province=province,
        category=category,
        is_active=True,
    )
