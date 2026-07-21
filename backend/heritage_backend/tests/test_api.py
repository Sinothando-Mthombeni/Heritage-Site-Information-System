"""
heritage_backend/tests/test_api.py

Integration tests for the HTTP API layer.
Uses Django's test Client to hit real URL routes and check:
  - correct status codes
  - response body shape
  - positive and negative (validation failure) paths

The active_site fixture (defined in conftest.py) provides a seeded
Province + Category + HeritageSite row for tests that need it.
"""
import json
from datetime import date, timedelta

import pytest
from django.test import Client

FUTURE_DATE  = (date.today() + timedelta(days=14)).isoformat()
PAST_DATE    = (date.today() - timedelta(days=1)).isoformat()
TODAY        = date.today().isoformat()


# ── Helpers ───────────────────────────────────────────────────────────────────

def valid_payload(site_id, **overrides):
    base = {
        "visitor_email":    "visitor@example.com",
        "visitor_name":     "Jane Doe",
        "site_id":          site_id,
        "visit_date":       FUTURE_DATE,
        "number_of_people": 2,
    }
    base.update(overrides)
    return base


def post_booking(payload):
    return Client().post(
        "/api/bookings/create/",
        data=json.dumps(payload),
        content_type="application/json",
    )


# ── Booking endpoint ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookingEndpoint:

    def test_valid_booking_returns_201(self, active_site):
        response = post_booking(valid_payload(active_site.site_id))
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "success"
        assert "booking_id" in body
        assert body["site"] == active_site.name
        assert body["number_of_people"] == 2

    def test_today_visit_date_is_accepted(self, active_site):
        response = post_booking(valid_payload(active_site.site_id, visit_date=TODAY))
        assert response.status_code == 201

    def test_repeat_visitor_reuses_existing_visitor_row(self, active_site):
        from heritage_backend.core.models import Visitor
        post_booking(valid_payload(active_site.site_id))
        post_booking(valid_payload(
            active_site.site_id,
            visit_date=(date.today() + timedelta(days=20)).isoformat(),
        ))
        assert Visitor.objects.filter(email="visitor@example.com").count() == 1

    def test_missing_visitor_email_returns_400(self, active_site):
        payload = valid_payload(active_site.site_id)
        del payload["visitor_email"]
        response = post_booking(payload)
        assert response.status_code == 400
        body = response.json()
        assert body["status"] == "error"
        assert "visitor_email" in body["errors"]

    def test_invalid_email_format_returns_400(self, active_site):
        response = post_booking(valid_payload(active_site.site_id, visitor_email="not-an-email"))
        assert response.status_code == 400
        assert "visitor_email" in response.json()["errors"]

    def test_missing_visitor_name_returns_400(self, active_site):
        payload = valid_payload(active_site.site_id)
        del payload["visitor_name"]
        response = post_booking(payload)
        assert response.status_code == 400
        assert "visitor_name" in response.json()["errors"]

    def test_blank_visitor_name_returns_400(self, active_site):
        response = post_booking(valid_payload(active_site.site_id, visitor_name="   "))
        assert response.status_code == 400
        assert "visitor_name" in response.json()["errors"]

    def test_past_visit_date_returns_400(self, active_site):
        response = post_booking(valid_payload(active_site.site_id, visit_date=PAST_DATE))
        assert response.status_code == 400
        assert "visit_date" in response.json()["errors"]

    def test_zero_people_returns_400(self, active_site):
        response = post_booking(valid_payload(active_site.site_id, number_of_people=0))
        assert response.status_code == 400
        assert "number_of_people" in response.json()["errors"]

    def test_negative_people_returns_400(self, active_site):
        response = post_booking(valid_payload(active_site.site_id, number_of_people=-3))
        assert response.status_code == 400
        assert "number_of_people" in response.json()["errors"]

    def test_nonexistent_site_id_returns_400(self):
        response = post_booking(valid_payload(99999))
        assert response.status_code == 400

    def test_invalid_json_body_returns_400(self):
        response = Client().post(
            "/api/bookings/create/",
            data="{not: valid json}",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.json()["status"] == "error"

    def test_empty_body_returns_400(self):
        response = Client().post(
            "/api/bookings/create/",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_get_request_returns_405(self):
        response = Client().get("/api/bookings/create/")
        assert response.status_code == 405


# ── Reporting endpoints ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReportingEndpoints:

    def test_bookings_per_site_returns_200_list(self, active_site):
        response = Client().get("/api/reports/bookings-per-site/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_bookings_per_site_reflects_created_booking(self, active_site):
        post_booking(valid_payload(active_site.site_id))
        response = Client().get("/api/reports/bookings-per-site/")
        assert response.status_code == 200
        names = [row["heritage_site__name"] for row in response.json()]
        assert active_site.name in names

    def test_average_group_size_returns_200_with_key(self):
        response = Client().get("/api/reports/average-group-size/")
        assert response.status_code == 200
        body = response.json()
        assert "average_group_size" in body
        assert isinstance(body["average_group_size"], (int, float))

    def test_average_group_size_zero_when_no_bookings(self):
        response = Client().get("/api/reports/average-group-size/")
        assert response.status_code == 200
        assert response.json()["average_group_size"] == 0

    def test_average_group_size_correct_after_booking(self, active_site):
        post_booking(valid_payload(active_site.site_id, number_of_people=4))
        response = Client().get("/api/reports/average-group-size/")
        assert response.status_code == 200
        assert response.json()["average_group_size"] == 4.0

    def test_monthly_stats_returns_200_list(self):
        response = Client().get("/api/reports/monthly-stats/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_monthly_stats_row_shape_after_booking(self, active_site):
        post_booking(valid_payload(active_site.site_id))
        response = Client().get("/api/reports/monthly-stats/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        row = data[0]
        assert "month" in row
        assert "total_bookings" in row

    def test_sites_with_provinces_returns_200_list(self, active_site):
        response = Client().get("/api/reports/sites/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_sites_with_provinces_response_shape(self, active_site):
        response = Client().get("/api/reports/sites/")
        first = response.json()[0]
        for key in ("site_id", "name", "province__name", "entry_fee"):
            assert key in first, f"Expected key '{key}' missing"
