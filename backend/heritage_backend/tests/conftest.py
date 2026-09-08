import pytest
from django.core.cache import cache

from heritage_backend.core.models import Category, HeritageSite, Province


@pytest.fixture(autouse=True)
def disable_rate_limiting(settings):
    """
    Rate limiting is a production security control, but it should not
    interfere with deterministic integration tests.
    """
    settings.RATELIMIT_ENABLE = False
    cache.clear()


@pytest.fixture
def active_site(db):
    """A single active HeritageSite for booking-related tests."""
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
