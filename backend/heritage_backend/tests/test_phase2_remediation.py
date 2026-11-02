import csv
import io
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import mongomock
import pytest
from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import Client
from django.utils import timezone

from heritage_backend.core.models import (
    Booking,
    Category,
    HeritageSite,
    Province,
    Visitor,
)


def create_booking(site, people, cancelled=False, email=None):
    visitor = Visitor.objects.create(
        full_name="Test Visitor",
        email=email or f"visitor-{Booking.objects.count()}@example.test",
    )
    return Booking.objects.create(
        heritage_site=site,
        visitor=visitor,
        visit_date=date.today(),
        number_of_people=people,
        is_cancelled=cancelled,
        cancelled_at=timezone.now() if cancelled else None,
    )


@pytest.mark.django_db
class TestSecurityContainment:
    def test_booking_export_is_denied_to_anonymous_users(self):
        response = Client().get("/api/reports/export/bookings/")
        assert response.status_code == 403
        assert response.json()["status"] == "error"

    def test_booking_export_is_denied_to_authenticated_nonstaff_users(self):
        user = get_user_model().objects.create_user(
            username="phase2-export-member",
            is_staff=False,
        )
        client = Client()
        client.force_login(user)
        response = client.get("/api/reports/export/bookings/")
        assert response.status_code == 403

    def test_staff_export_preserves_csv_contract_and_neutralizes_formulas(
        self, active_site
    ):
        active_site.name = "\u00a0@formula"
        active_site.save(update_fields=["name"])
        visitor = Visitor.objects.create(
            full_name=" \t=1+1, \nRich",
            email="=1+1@example.test",
        )
        booking = Booking.objects.create(
            visitor=visitor,
            heritage_site=active_site,
            visit_date=date.today(),
            number_of_people=2,
        )
        staff_user = get_user_model().objects.create_user(
            username="phase2-export-staff",
            is_staff=True,
        )
        client = Client()
        client.force_login(staff_user)

        response = client.get("/api/reports/export/bookings/")
        rows = list(csv.reader(io.StringIO(
            b"".join(response.streaming_content).decode(response.charset or "utf-8")
        )))

        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/csv")
        assert response["Content-Disposition"] == "attachment; filename=bookings.csv"
        assert rows[0] == [
            "booking_id",
            "visitor_name",
            "visitor_email",
            "site_name",
            "visit_date",
            "number_of_people",
            "booking_date",
            "is_cancelled",
        ]
        assert rows[1] == [
            str(booking.booking_id),
            "' \t=1+1, \nRich",
            "'=1+1@example.test",
            "'\u00a0@formula",
            str(booking.visit_date),
            "2",
            str(booking.booking_date),
            "False",
        ]

    def test_public_booking_cancellation_is_disabled(self):
        with patch(
            "heritage_backend.services.booking_service.cancel_booking"
        ) as cancel_booking:
            response = Client().patch("/api/bookings/123/cancel/")
        assert response.status_code == 503
        assert cancel_booking.call_count == 0

    def test_cancellation_rejects_non_patch_methods(self):
        response = Client().get("/api/bookings/123/cancel/")
        assert response.status_code == 405

    def test_staff_export_of_empty_bookings_contains_headers_only(self):
        user = get_user_model().objects.create_user(
            username="phase2-empty-export-staff",
            is_staff=True,
        )
        client = Client()
        client.force_login(user)
        response = client.get("/api/reports/export/bookings/")
        rows = list(csv.reader(io.StringIO(
            b"".join(response.streaming_content).decode(response.charset or "utf-8")
        )))
        assert response.status_code == 200
        assert rows == [[
            "booking_id",
            "visitor_name",
            "visitor_email",
            "site_name",
            "visit_date",
            "number_of_people",
            "booking_date",
            "is_cancelled",
        ]]


@pytest.mark.django_db
class TestBookingReportSemantics:
    def test_cancelled_bookings_are_excluded_and_duplicate_site_names_are_distinct(
        self, active_site
    ):
        second_province = Province.objects.create(name="Other Province")
        second_site = HeritageSite.objects.create(
            name=active_site.name,
            description="A same-named site in a different province.",
            entry_fee=active_site.entry_fee,
            is_active=True,
            province=second_province,
            category=active_site.category,
        )
        first_booking = create_booking(active_site, 2)
        first_booking.visit_date = date(2030, 4, 1)
        first_booking.save(update_fields=["visit_date"])
        create_booking(active_site, 4)
        create_booking(active_site, 100, cancelled=True)
        create_booking(second_site, 6)

        client = Client()
        by_site = client.get("/api/reports/bookings-per-site/")
        average = client.get("/api/reports/average-group-size/")
        monthly = client.get("/api/reports/monthly-stats/")

        assert by_site.status_code == 200
        assert [
            (row["heritage_site_id"], row["heritage_site__name"], row["total"])
            for row in by_site.json()
        ] == [
            (active_site.site_id, active_site.name, 2),
            (second_site.site_id, second_site.name, 1),
        ]
        assert average.json() == {"average_group_size": 4.0}
        assert monthly.json() == [{
            "month": timezone.now().date().strftime("%Y-%m"),
            "total_bookings": 3,
        }]

    def test_postgresql_and_mongodb_booking_reports_match(self, active_site):
        second_province = Province.objects.create(name="Second Province")
        second_site = HeritageSite.objects.create(
            name=active_site.name,
            description="Duplicate name for aggregation identity coverage.",
            entry_fee=active_site.entry_fee,
            is_active=True,
            province=second_province,
            category=active_site.category,
        )
        create_booking(active_site, 2)
        create_booking(active_site, 4)
        create_booking(active_site, 50, cancelled=True)
        create_booking(second_site, 6)

        mongo_bookings = mongomock.MongoClient().heritage_phase2_test.bookings
        mongo_bookings.insert_many([
            {
                "site_id": booking.heritage_site_id,
                "site_name": booking.heritage_site.name,
                "province": booking.heritage_site.province.name,
                "visitors": booking.number_of_people,
                "booking_date": booking.booking_date.isoformat(),
                "is_cancelled": booking.is_cancelled,
            }
            for booking in Booking.objects.select_related(
                "heritage_site__province"
            ).order_by("booking_id")
        ])

        from mongo.analytics import (
            average_group_size,
            bookings_per_site,
            monthly_booking_stats,
        )
        from heritage_backend.services.reporting_service import (
            average_group_size as pg_average_group_size,
            bookings_per_site as pg_bookings_per_site,
            monthly_booking_stats as pg_monthly_booking_stats,
        )

        pg_site_rows = list(pg_bookings_per_site())
        mongo_site_rows = bookings_per_site(mongo_bookings)
        assert [
            (row["heritage_site_id"], row["heritage_site__name"], row["total"])
            for row in pg_site_rows
        ] == [
            (row["heritage_site_id"], row["heritage_site__name"], row["total"])
            for row in mongo_site_rows
        ]
        assert round(float(pg_average_group_size()["avg_people"]), 2) == (
            average_group_size(mongo_bookings)
        )
        assert [
            (row[0].strftime("%Y-%m"), row[1])
            for row in pg_monthly_booking_stats()
        ] == [
            (row["month"], row["total_bookings"])
            for row in monthly_booking_stats(mongo_bookings)
        ]

    def test_public_catalogue_excludes_inactive_sites(self, active_site):
        inactive_site = HeritageSite.objects.create(
            name="Inactive site",
            description="Not visible in the public catalogue.",
            entry_fee=20,
            is_active=False,
            province=active_site.province,
            category=active_site.category,
        )
        response = Client().get("/api/reports/sites/")
        assert response.status_code == 200
        site_ids = {row["site_id"] for row in response.json()}
        assert active_site.site_id in site_ids
        assert inactive_site.site_id not in site_ids

    def test_public_site_detail_and_counts_exclude_inactive_sites(self, active_site):
        inactive_province = Province.objects.create(name="Inactive Province")
        inactive_category = Category.objects.create(
            name="Inactive Category"
        )
        inactive_site = HeritageSite.objects.create(
            name="Inactive only",
            description="Not exposed by public endpoints.",
            entry_fee=10,
            is_active=False,
            province=inactive_province,
            category=inactive_category,
        )

        active_detail = Client().get(f"/api/sites/{active_site.site_id}/")
        inactive_detail = Client().get(f"/api/sites/{inactive_site.site_id}/")
        missing_detail = Client().get("/api/sites/999999/")
        province_counts = Client().get("/api/reports/province-counts/").json()
        category_counts = Client().get("/api/reports/category-counts/").json()

        assert active_detail.status_code == 200
        assert inactive_detail.status_code == 404
        assert missing_detail.status_code == 404
        assert province_counts == [{
            "province__name": active_site.province.name,
            "count": 1,
        }]
        assert category_counts == [{
            "category__name": active_site.category.name,
            "count": 1,
        }]

    @pytest.mark.parametrize(
        "path",
        [
            "/api/reports/bookings-per-site/",
            "/api/reports/average-group-size/",
            "/api/reports/monthly-stats/",
            "/api/reports/sites/",
            "/api/reports/province-counts/",
            "/api/reports/category-counts/",
            "/api/reports/featured/",
            "/api/reports/export/bookings/",
            "/api/sites/1/",
        ],
    )
    def test_read_only_post_requests_return_405(self, path):
        assert Client().post(path).status_code == 405


class TestSafeApiErrors:
    @pytest.mark.django_db
    def test_unknown_site_id_returns_a_sanitized_validation_error(self):
        response = Client().post(
            "/api/bookings/create/",
            data=(
                '{"visitor_email":"visitor@example.test",'
                '"visitor_name":"Test","site_id":999999,'
                '"visit_date":"2030-01-01","number_of_people":2}'
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.json()["errors"]["site_id"] == [
            "The selected site is unavailable."
        ]
        assert Visitor.objects.count() == 0

    def test_booking_rejects_non_json_content_type(self):
        response = Client().post(
            "/api/bookings/create/",
            data={"visitor_email": "visitor@example.test"},
        )
        assert response.status_code == 415

    def test_database_error_returns_sanitized_503(self):
        with patch(
            "api.views_pg.create_booking",
            side_effect=OperationalError("private connection detail"),
        ):
            response = Client().post(
                "/api/bookings/create/",
                data=(
                    '{"visitor_email":"visitor@example.test",'
                    '"visitor_name":"Test","site_id":1,'
                    '"visit_date":"2030-01-01","number_of_people":2}'
                ),
                content_type="application/json",
            )
        assert response.status_code == 503
        assert "private connection detail" not in response.content.decode()

    def test_unexpected_error_returns_sanitized_500(self):
        with patch(
            "api.views_pg.create_booking",
            side_effect=RuntimeError("private implementation detail"),
        ):
            response = Client().post(
                "/api/bookings/create/",
                data=(
                    '{"visitor_email":"visitor@example.test",'
                    '"visitor_name":"Test","site_id":1,'
                    '"visit_date":"2030-01-01","number_of_people":2}'
                ),
                content_type="application/json",
            )
        assert response.status_code == 500
        assert "private implementation detail" not in response.content.decode()


def test_production_secret_key_configuration_rejects_missing_and_development_keys():
    from django.core.exceptions import ImproperlyConfigured
    from settings import _resolve_secret_key

    with pytest.raises(ImproperlyConfigured):
        _resolve_secret_key(None, debug=False)
    with pytest.raises(ImproperlyConfigured):
        _resolve_secret_key("insecure-dev-key", debug=False)
    with pytest.raises(ImproperlyConfigured):
        _resolve_secret_key(
            "replace-with-a-long-random-string-at-least-50-chars", debug=False
        )
    with pytest.raises(ImproperlyConfigured):
        _resolve_secret_key("   ", debug=False)
    assert _resolve_secret_key("insecure-dev-key", debug=True) == "insecure-dev-key"
    assert _resolve_secret_key("configured-key", debug=False) == "configured-key"


def test_test_settings_reject_database_urls_and_nonlocal_services():
    cases = [
        (
            {"DATABASE_URL": "postgresql://example.invalid/database"},
            "inherited database URL variables",
        ),
        (
            {"HERITAGE_TEST_DB_HOST": "db.example.invalid"},
            "isolated local PostgreSQL service",
        ),
        (
            {"HERITAGE_TEST_MONGO_URI": "mongodb+srv://example.invalid/"},
            "isolated local MongoDB service",
        ),
    ]
    backend_dir = Path(__file__).resolve().parents[2]
    for overrides, error_message in cases:
        environment = os.environ.copy()
        for name in (
            "DATABASE_URL",
            "NEON_DATABASE_URL",
            "NEON_DATABASE_URL_UNPOOLED",
            "RESTORE_DATABASE_URL",
        ):
            environment.pop(name, None)
        for name in tuple(environment):
            if name.startswith("HERITAGE_TEST_"):
                environment.pop(name)
        environment.update(overrides)
        environment["DJANGO_SETTINGS_MODULE"] = "test_settings"
        result = subprocess.run(
            [sys.executable, "-c", "import test_settings"],
            cwd=backend_dir,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert error_message in result.stderr
