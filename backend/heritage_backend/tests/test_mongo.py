"""Mongo analytics and API tests using isolated mongomock collections."""
import pytest
import mongomock
from unittest.mock import patch

from django.test import Client


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_collection():
    """Empty in-memory MongoDB collection."""
    client = mongomock.MongoClient()
    db = client["heritage_phase2_test"]
    return db.heritage_sites


@pytest.fixture
def seeded_collection(mock_collection):
    """Collection pre-populated with two representative SA heritage sites."""
    mock_collection.insert_many([
        {
            "site_id":     1,
            "name":        "Robben Island",
            "province":    "Western Cape",
            "category":    "UNESCO World Heritage Site",
            "entry_fee":   880.0,
            "is_active":   True,
            "description": "Historic maximum-security prison island in Table Bay.",
        },
        {
            "site_id":     2,
            "name":        "Cradle of Humankind",
            "province":    "Gauteng",
            "category":    "UNESCO World Heritage Site",
            "entry_fee":   170.0,
            "is_active":   True,
            "description": "World-famous paleoanthropological site near Johannesburg.",
        },
    ])
    return mock_collection


# ─── Analytics unit tests ─────────────────────────────────────────────────────

class TestAverageEntryFee:

    def test_empty_collection_returns_zero(self, mock_collection):
        """With no documents, the function must return 0, not crash."""
        with patch("mongo.analytics.active_collection", return_value=mock_collection):
            from mongo.analytics import average_entry_fee
            assert average_entry_fee() == 0

    def test_correct_average_with_two_sites(self, seeded_collection):
        """(880 + 170) / 2 = 525.0"""
        with patch("mongo.analytics.active_collection", return_value=seeded_collection):
            from mongo.analytics import average_entry_fee
            result = average_entry_fee()
            assert result == pytest.approx(525.0, rel=1e-3)

    def test_null_entry_fee_excluded_from_average(self, mock_collection):
        """Sites with entry_fee=None must not affect the average."""
        mock_collection.insert_many([
            {"site_id": 10, "entry_fee": 200.0, "is_active": True},
            {"site_id": 11, "entry_fee": None, "is_active": True},
        ])
        with patch("mongo.analytics.active_collection", return_value=mock_collection):
            from mongo.analytics import average_entry_fee
            assert average_entry_fee() == pytest.approx(200.0)

    def test_single_site_returns_its_own_fee(self, mock_collection):
        mock_collection.insert_one(
            {"site_id": 20, "entry_fee": 350.0, "is_active": True}
        )
        with patch("mongo.analytics.active_collection", return_value=mock_collection):
            from mongo.analytics import average_entry_fee
            assert average_entry_fee() == pytest.approx(350.0)

    def test_inactive_sites_are_excluded(self, mock_collection):
        mock_collection.insert_many([
            {"site_id": 1, "entry_fee": 100.0, "is_active": True},
            {"site_id": 2, "entry_fee": 900.0, "is_active": False},
        ])
        from mongo.analytics import average_entry_fee
        assert average_entry_fee(mock_collection) == pytest.approx(100.0)

    def test_no_active_site_returns_zero(self, mock_collection):
        mock_collection.insert_one(
            {"site_id": 1, "entry_fee": 900.0, "is_active": False}
        )
        from mongo.analytics import average_entry_fee
        assert average_entry_fee(mock_collection) == 0


class TestSitesPerProvince:

    def test_empty_collection_returns_empty_list(self, mock_collection):
        with patch("mongo.analytics.active_collection", return_value=mock_collection):
            from mongo.analytics import sites_per_province
            assert sites_per_province() == []

    def test_groups_by_province_correctly(self, seeded_collection):
        with patch("mongo.analytics.active_collection", return_value=seeded_collection):
            from mongo.analytics import sites_per_province
            result = sites_per_province()
            assert len(result) == 2
            province_names = {r["_id"] for r in result}
            assert "Western Cape" in province_names
            assert "Gauteng" in province_names

    def test_count_is_correct_per_province(self, mock_collection):
        """Two sites in Gauteng, one in Western Cape → counts must match."""
        mock_collection.insert_many([
            {"site_id": 1, "province": "Gauteng", "is_active": True},
            {"site_id": 2, "province": "Gauteng", "is_active": True},
            {"site_id": 3, "province": "Western Cape", "is_active": True},
        ])
        with patch("mongo.analytics.active_collection", return_value=mock_collection):
            from mongo.analytics import sites_per_province
            result = sites_per_province()
            by_province = {r["_id"]: r["count"] for r in result}
            assert by_province["Gauteng"] == 2
            assert by_province["Western Cape"] == 1

    def test_ordered_by_count_descending(self, mock_collection):
        """Province with most sites should appear first."""
        mock_collection.insert_many([
            {"site_id": 1, "province": "Western Cape", "is_active": True},
            {"site_id": 2, "province": "Gauteng", "is_active": True},
            {"site_id": 3, "province": "Gauteng", "is_active": True},
            {"site_id": 4, "province": "Gauteng", "is_active": True},
        ])
        with patch("mongo.analytics.active_collection", return_value=mock_collection):
            from mongo.analytics import sites_per_province
            result = sites_per_province()
            assert result[0]["_id"] == "Gauteng"   # 3 sites → first
            assert result[0]["count"] == 3

    def test_inactive_sites_and_empty_provinces_are_excluded(self, mock_collection):
        mock_collection.insert_many([
            {"site_id": 1, "province": "Active Province", "is_active": True},
            {"site_id": 2, "province": "Active Province", "is_active": False},
            {"site_id": 3, "province": "No Active Sites", "is_active": False},
        ])
        from mongo.analytics import sites_per_province
        assert sites_per_province(mock_collection) == [
            {"_id": "Active Province", "count": 1}
        ]


# ─── Mongo API endpoint integration tests ─────────────────────────────────────

@pytest.mark.django_db
class TestMongoSitesEndpoints:

    def test_all_sites_empty_collection_returns_empty_list(self, mock_collection):
        with patch("mongo.heritage_sites.active_collection", return_value=mock_collection):
            response = Client().get("/api/mongo/sites/")
            assert response.status_code == 200
            assert response.json() == []

    def test_all_sites_returns_seeded_documents(self, seeded_collection):
        with patch("mongo.heritage_sites.active_collection", return_value=seeded_collection):
            response = Client().get("/api/mongo/sites/")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            names = {s["name"] for s in data}
            assert "Robben Island" in names
            assert "Cradle of Humankind" in names

    def test_all_sites_excludes_mongo_id_field(self, seeded_collection):
        """_id must be projection-excluded so it doesn't appear in responses."""
        with patch("mongo.heritage_sites.active_collection", return_value=seeded_collection):
            response = Client().get("/api/mongo/sites/")
            for site in response.json():
                assert "_id" not in site

    def test_sites_pagination_is_stable_and_filters_inactive_sites(
        self, seeded_collection
    ):
        seeded_collection.insert_many([
            {
                "site_id": 3,
                "name": "Inactive",
                "province": "Gauteng",
                "is_active": False,
            },
            {
                "site_id": 4,
                "name": "Site Four",
                "province": "Gauteng",
                "is_active": True,
            },
        ])
        with patch(
            "mongo.heritage_sites.active_collection", return_value=seeded_collection
        ):
            first = Client().get("/api/mongo/sites/?page=1&page_size=1")
            second = Client().get("/api/mongo/sites/?page=2&page_size=1")
        assert [row["site_id"] for row in first.json()] == [1]
        assert [row["site_id"] for row in second.json()] == [2]

    def test_pagination_defaults_and_maximum_page_size(self, seeded_collection):
        seeded_collection.insert_many([
            {
                "site_id": site_id,
                "name": f"Site {site_id}",
                "is_active": True,
            }
            for site_id in range(3, 102)
        ])
        with patch(
            "mongo.heritage_sites.active_collection", return_value=seeded_collection
        ):
            default_page = Client().get("/api/mongo/sites/")
            max_page = Client().get("/api/mongo/sites/?page_size=100")
            second_max_page = Client().get(
                "/api/mongo/sites/?page=2&page_size=100"
            )
        assert len(default_page.json()) == 10
        assert len(max_page.json()) == 100
        assert len(second_max_page.json()) == 1

    @pytest.mark.parametrize(
        "query",
        [
            "?page=0",
            "?page=-1",
            "?page=abc",
            "?page=9223372036854775808&page_size=100",
            "?page_size=0",
            "?page_size=101",
            "?page_size=not-a-number",
        ],
    )
    def test_invalid_pagination_returns_400(self, seeded_collection, query):
        with patch(
            "mongo.heritage_sites.active_collection", return_value=seeded_collection
        ):
            response = Client().get(f"/api/mongo/sites/{query}")
        assert response.status_code == 400
        assert response.json()["status"] == "error"

    def test_filter_by_province_returns_matching_sites(self, seeded_collection):
        with patch("mongo.heritage_sites.active_collection", return_value=seeded_collection):
            response = Client().get("/api/mongo/sites/province/Gauteng/")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Cradle of Humankind"
            assert data[0]["province"] == "Gauteng"

    def test_filter_by_province_nonexistent_returns_empty(self, seeded_collection):
        with patch("mongo.heritage_sites.active_collection", return_value=seeded_collection):
            response = Client().get("/api/mongo/sites/province/Limpopo/")
            assert response.status_code == 200
            assert response.json() == []

    def test_site_detail_by_name_returns_correct_site(self, seeded_collection):
        with patch("mongo.heritage_sites.active_collection", return_value=seeded_collection):
            response = Client().get("/api/mongo/sites/Robben Island/")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Robben Island"
            assert data["province"] == "Western Cape"
            assert data["entry_fee"] == 880.0

    def test_site_detail_nonexistent_returns_404(self, seeded_collection):
        with patch("mongo.heritage_sites.active_collection", return_value=seeded_collection):
            response = Client().get("/api/mongo/sites/Nonexistent Site/")
            assert response.status_code == 404
            assert response.json()["message"] == "Site not found."

    @pytest.mark.parametrize(
        "path",
        [
            "/api/mongo/sites/",
            "/api/mongo/sites/province/Gauteng/",
            "/api/mongo/sites/Robben Island/",
            "/api/mongo/analytics/sites-per-province/",
            "/api/mongo/analytics/average-fee/",
        ],
    )
    def test_read_endpoints_reject_post(self, path):
        assert Client().post(path).status_code == 405


@pytest.mark.django_db
class TestMongoAnalyticsEndpoints:

    def test_average_fee_endpoint_returns_correct_value(self, seeded_collection):
        with patch("mongo.analytics.active_collection", return_value=seeded_collection):
            response = Client().get("/api/mongo/analytics/average-fee/")
            assert response.status_code == 200
            data = response.json()
            assert "average_fee" in data
            assert data["average_fee"] == pytest.approx(525.0, rel=1e-3)

    def test_average_fee_endpoint_empty_collection(self, mock_collection):
        with patch("mongo.analytics.active_collection", return_value=mock_collection):
            response = Client().get("/api/mongo/analytics/average-fee/")
            assert response.status_code == 200
            assert response.json()["average_fee"] == 0

    def test_sites_per_province_endpoint_returns_list(self, seeded_collection):
        with patch("mongo.analytics.active_collection", return_value=seeded_collection):
            response = Client().get("/api/mongo/analytics/sites-per-province/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2

    def test_sites_per_province_endpoint_row_shape(self, seeded_collection):
        """Each row must have '_id' (province name) and 'count' keys."""
        with patch("mongo.analytics.active_collection", return_value=seeded_collection):
            response = Client().get("/api/mongo/analytics/sites-per-province/")
            assert response.status_code == 200
            row = response.json()[0]
            assert "_id" in row
            assert "count" in row

    def test_inactive_sites_are_excluded_from_public_analytics(self, mock_collection):
        mock_collection.insert_many([
            {
                "site_id": 1,
                "province": "Active Province",
                "entry_fee": 100.0,
                "is_active": True,
            },
            {
                "site_id": 2,
                "province": "Active Province",
                "entry_fee": 900.0,
                "is_active": False,
            },
            {
                "site_id": 3,
                "province": "Inactive Province",
                "entry_fee": 500.0,
                "is_active": False,
            },
        ])
        with patch("mongo.analytics.active_collection", return_value=mock_collection):
            counts = Client().get(
                "/api/mongo/analytics/sites-per-province/"
            ).json()
            fee = Client().get("/api/mongo/analytics/average-fee/").json()
        assert counts == [{"_id": "Active Province", "count": 1}]
        assert fee == {"average_fee": 100.0}

    def test_unavailable_mongo_returns_sanitized_503(self):
        from pymongo.errors import PyMongoError
        with patch(
            "api.views_mongo.sites_per_province",
            side_effect=PyMongoError("private connection detail"),
        ):
            response = Client().get("/api/mongo/analytics/sites-per-province/")
        assert response.status_code == 503
        assert "private connection detail" not in response.content.decode()


class TestMongoBookingReports:
    def test_cancelled_bookings_are_excluded_and_site_identity_is_stable(
        self, mock_collection
    ):
        mock_collection.insert_many([
            {
                "booking_id": 1,
                "site_id": 1,
                "site_name": "Twin Site",
                "province": "Province A",
                "visitors": 2,
                "booking_date": "2025-02-01",
                "is_cancelled": False,
            },
            {
                "booking_id": 2,
                "site_id": 1,
                "site_name": "Twin Site",
                "province": "Province A",
                "visitors": 4,
                "booking_date": "2025-02-18",
                "is_cancelled": False,
            },
            {
                "booking_id": 3,
                "site_id": 1,
                "site_name": "Twin Site",
                "province": "Province A",
                "visitors": 100,
                "booking_date": "2025-02-20",
                "is_cancelled": True,
            },
            {
                "booking_id": 4,
                "site_id": 2,
                "site_name": "Twin Site",
                "province": "Province B",
                "visitors": 6,
                "booking_date": "2025-03-01",
                "is_cancelled": False,
            },
        ])
        from mongo.analytics import (
            average_group_size,
            bookings_per_site,
            monthly_booking_stats,
        )

        assert bookings_per_site(mock_collection) == [
            {
                "heritage_site_id": 1,
                "heritage_site__name": "Twin Site",
                "heritage_site__province__name": "Province A",
                "total": 2,
            },
            {
                "heritage_site_id": 2,
                "heritage_site__name": "Twin Site",
                "heritage_site__province__name": "Province B",
                "total": 1,
            },
        ]
        assert average_group_size(mock_collection) == 4.0
        assert monthly_booking_stats(mock_collection) == [
            {"month": "2025-02", "total_bookings": 2},
            {"month": "2025-03", "total_bookings": 1},
        ]

    def test_empty_booking_reports_return_zero_or_empty_list(self, mock_collection):
        from mongo.analytics import (
            average_group_size,
            bookings_per_site,
            monthly_booking_stats,
        )
        assert bookings_per_site(mock_collection) == []
        assert average_group_size(mock_collection) == 0
        assert monthly_booking_stats(mock_collection) == []
