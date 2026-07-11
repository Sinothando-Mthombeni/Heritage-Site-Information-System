import json
import pytest
from django.test import Client
from heritage_backend.tests.conftest import *  # reuse active_site fixture

@pytest.mark.django_db
def test_create_booking_returns_201(active_site):
    client = Client()
    response = client.post(
        "/api/bookings/create/",
        data=json.dumps({
            "visitor_email": "api@test.com",
            "visitor_name": "API Tester",
            "site_id": active_site.site_id,
            "visit_date": "2026-09-01",
            "number_of_people": 3,
        }),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["status"] == "success"

@pytest.mark.django_db
def test_create_booking_missing_field_returns_400(active_site):
    client = Client()
    response = client.post(
        "/api/bookings/create/",
        data=json.dumps({"visitor_email": "x@x.com"}),
        content_type="application/json",
    )
    assert response.status_code == 400

@pytest.mark.django_db
def test_sites_with_provinces_returns_data(active_site):
    client = Client()
    response = client.get("/api/reports/sites/")
    assert response.status_code == 200
    assert len(response.json()) >= 1