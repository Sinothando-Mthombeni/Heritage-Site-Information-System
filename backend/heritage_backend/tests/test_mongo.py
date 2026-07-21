"""
heritage_backend/tests/test_mongo.py

MongoDB test suite using mongomock — no live Mongo instance required.

Two patch targets, based on module-level collection objects:
  - mongo.analytics.heritage_sites      → used by analytics functions
  - mongo.heritage_sites.heritage_sites_collection → used by query helpers
                                                      (and indirectly by views)

Structure:
  TestAverageEntryFee     — unit tests for the aggregation pipeline
  TestSitesPerProvince    — unit tests for the grouping pipeline
  TestMongoSitesEndpoints — integration tests for /api/mongo/sites/* routes
  TestMongoAnalyticsEndpoints — integration tests for /api/mongo/analytics/* routes
"""
import pytest
import mongomock
from unittest.mock import patch

from django.test import Client


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_collection():
    """Empty in-memory MongoDB collection."""
    client = mongomock.MongoClient()
    db = client["heritage_phase3"]
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
        with patch("mongo.analytics.heritage_sites", mock_collection):
            from mongo.analytics import average_entry_fee
            assert average_entry_fee() == 0

    def test_correct_average_with_two_sites(self, seeded_collection):
        """(880 + 170) / 2 = 525.0"""
        with patch("mongo.analytics.heritage_sites", seeded_collection):
            from mongo.analytics import average_entry_fee
            result = average_entry_fee()
            assert result == pytest.approx(525.0, rel=1e-3)

    def test_null_entry_fee_excluded_from_average(self, mock_collection):
        """Sites with entry_fee=None must not affect the average."""
        mock_collection.insert_many([
            {"site_id": 10, "entry_fee": 200.0},
            {"site_id": 11, "entry_fee": None},   # should be excluded by $match
        ])
        with patch("mongo.analytics.heritage_sites", mock_collection):
            from mongo.analytics import average_entry_fee
            assert average_entry_fee() == pytest.approx(200.0)

    def test_single_site_returns_its_own_fee(self, mock_collection):
        mock_collection.insert_one({"site_id": 20, "entry_fee": 350.0})
        with patch("mongo.analytics.heritage_sites", mock_collection):
            from mongo.analytics import average_entry_fee
            assert average_entry_fee() == pytest.approx(350.0)


class TestSitesPerProvince:

    def test_empty_collection_returns_empty_list(self, mock_collection):
        with patch("mongo.analytics.heritage_sites", mock_collection):
            from mongo.analytics import sites_per_province
            assert sites_per_province() == []

    def test_groups_by_province_correctly(self, seeded_collection):
        with patch("mongo.analytics.heritage_sites", seeded_collection):
            from mongo.analytics import sites_per_province
            result = sites_per_province()
            assert len(result) == 2
            province_names = {r["_id"] for r in result}
            assert "Western Cape" in province_names
            assert "Gauteng" in province_names

    def test_count_is_correct_per_province(self, mock_collection):
        """Two sites in Gauteng, one in Western Cape → counts must match."""
        mock_collection.insert_many([
            {"site_id": 1, "province": "Gauteng"},
            {"site_id": 2, "province": "Gauteng"},
            {"site_id": 3, "province": "Western Cape"},
        ])
        with patch("mongo.analytics.heritage_sites", mock_collection):
            from mongo.analytics import sites_per_province
            result = sites_per_province()
            by_province = {r["_id"]: r["count"] for r in result}
            assert by_province["Gauteng"] == 2
            assert by_province["Western Cape"] == 1

    def test_ordered_by_count_descending(self, mock_collection):
        """Province with most sites should appear first."""
        mock_collection.insert_many([
            {"site_id": 1, "province": "Western Cape"},
            {"site_id": 2, "province": "Gauteng"},
            {"site_id": 3, "province": "Gauteng"},
            {"site_id": 4, "province": "Gauteng"},
        ])
        with patch("mongo.analytics.heritage_sites", mock_collection):
            from mongo.analytics import sites_per_province
            result = sites_per_province()
            assert result[0]["_id"] == "Gauteng"   # 3 sites → first
            assert result[0]["count"] == 3


# ─── Mongo API endpoint integration tests ─────────────────────────────────────

@pytest.mark.django_db
class TestMongoSitesEndpoints:

    def test_all_sites_empty_collection_returns_empty_list(self, mock_collection):
        with patch("mongo.heritage_sites.heritage_sites_collection", mock_collection):
            response = Client().get("/api/mongo/sites/")
            assert response.status_code == 200
            assert response.json() == []

    def test_all_sites_returns_seeded_documents(self, seeded_collection):
        with patch("mongo.heritage_sites.heritage_sites_collection", seeded_collection):
            response = Client().get("/api/mongo/sites/")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            names = {s["name"] for s in data}
            assert "Robben Island" in names
            assert "Cradle of Humankind" in names

    def test_all_sites_excludes_mongo_id_field(self, seeded_collection):
        """_id must be projection-excluded so it doesn't appear in responses."""
        with patch("mongo.heritage_sites.heritage_sites_collection", seeded_collection):
            response = Client().get("/api/mongo/sites/")
            for site in response.json():
                assert "_id" not in site

    def test_filter_by_province_returns_matching_sites(self, seeded_collection):
        with patch("mongo.heritage_sites.heritage_sites_collection", seeded_collection):
            response = Client().get("/api/mongo/sites/province/Gauteng/")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Cradle of Humankind"
            assert data[0]["province"] == "Gauteng"

    def test_filter_by_province_nonexistent_returns_empty(self, seeded_collection):
        with patch("mongo.heritage_sites.heritage_sites_collection", seeded_collection):
            response = Client().get("/api/mongo/sites/province/Limpopo/")
            assert response.status_code == 200
            assert response.json() == []

    def test_site_detail_by_name_returns_correct_site(self, seeded_collection):
        with patch("mongo.heritage_sites.heritage_sites_collection", seeded_collection):
            response = Client().get("/api/mongo/sites/Robben Island/")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Robben Island"
            assert data["province"] == "Western Cape"
            assert data["entry_fee"] == 880.0

    def test_site_detail_nonexistent_returns_empty_dict(self, seeded_collection):
        with patch("mongo.heritage_sites.heritage_sites_collection", seeded_collection):
            response = Client().get("/api/mongo/sites/Nonexistent Site/")
            assert response.status_code == 200
            assert response.json() == {}


@pytest.mark.django_db
class TestMongoAnalyticsEndpoints:

    def test_average_fee_endpoint_returns_correct_value(self, seeded_collection):
        with patch("mongo.analytics.heritage_sites", seeded_collection):
            response = Client().get("/api/mongo/analytics/average-fee/")
            assert response.status_code == 200
            data = response.json()
            assert "average_fee" in data
            assert data["average_fee"] == pytest.approx(525.0, rel=1e-3)

    def test_average_fee_endpoint_empty_collection(self, mock_collection):
        with patch("mongo.analytics.heritage_sites", mock_collection):
            response = Client().get("/api/mongo/analytics/average-fee/")
            assert response.status_code == 200
            assert response.json()["average_fee"] == 0

    def test_sites_per_province_endpoint_returns_list(self, seeded_collection):
        with patch("mongo.analytics.heritage_sites", seeded_collection):
            response = Client().get("/api/mongo/analytics/sites-per-province/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2

    def test_sites_per_province_endpoint_row_shape(self, seeded_collection):
        """Each row must have '_id' (province name) and 'count' keys."""
        with patch("mongo.analytics.heritage_sites", seeded_collection):
            response = Client().get("/api/mongo/analytics/sites-per-province/")
            assert response.status_code == 200
            row = response.json()[0]
            assert "_id" in row
            assert "count" in row
