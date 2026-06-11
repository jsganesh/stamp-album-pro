"""
Tests for the stamp collection API and CSV import.
"""
import io
import pytest
from fastapi.testclient import TestClient

from stamp_album.api import app
from stamp_album.collection import COLLECTION_FILE


@pytest.fixture(autouse=True)
def clean_collection():
    """Clean up the collection file before each test."""
    if COLLECTION_FILE.exists():
        COLLECTION_FILE.unlink()
    yield
    if COLLECTION_FILE.exists():
        COLLECTION_FILE.unlink()


@pytest.fixture
def client():
    return TestClient(app)


class TestCollectionCRUD:
    """Tests for stamp collection CRUD operations."""

    def test_empty_collection(self, client):
        response = client.get("/api/stamps")
        assert response.status_code == 200
        data = response.json()
        assert data["stamps"] == []
        assert data["total"] == 0

    def test_add_stamp(self, client):
        stamp_data = {
            "country": "Great Britain",
            "year": 1840,
            "description": "Penny Black",
            "catalog_number": "SG 1",
            "catalog_type": "SG",
            "denomination": "1d",
            "condition": "Used",
            "purchase_price": 250.0,
            "notes": "First postage stamp",
        }
        response = client.post("/api/stamps", json=stamp_data)
        assert response.status_code == 200
        result = response.json()
        assert result["country"] == "Great Britain"
        assert result["description"] == "Penny Black"
        assert result["id"] is not None

    def test_list_stamps(self, client):
        # Add a stamp first
        client.post("/api/stamps", json={
            "country": "France", "year": 1849, "description": "Ceres",
            "catalog_number": "SG 1", "catalog_type": "SG",
        })
        response = client.get("/api/stamps")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_search_stamps(self, client):
        client.post("/api/stamps", json={
            "country": "Germany", "year": 1872, "description": "Eagle issue",
            "catalog_number": "SG 1", "catalog_type": "SG",
        })
        response = client.get("/api/stamps", params={"query": "Eagle"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_filter_by_country(self, client):
        response = client.get("/api/stamps", params={"country": "Germany"})
        assert response.status_code == 200
        data = response.json()
        for s in data["stamps"]:
            assert s["country"] == "Germany"

    def test_update_stamp(self, client):
        # Create
        create_resp = client.post("/api/stamps", json={
            "country": "Italy", "year": 1862, "description": "Sardinia issue",
            "catalog_number": "SG 1", "catalog_type": "SG",
        })
        stamp_id = create_resp.json()["id"]

        # Update
        response = client.put(f"/api/stamps/{stamp_id}", json={
            "description": "Updated description",
            "purchase_price": 100.0,
        })
        assert response.status_code == 200
        result = response.json()
        assert result["description"] == "Updated description"
        assert result["purchase_price"] == 100.0
        # Unchanged fields preserved
        assert result["country"] == "Italy"

    def test_delete_stamp(self, client):
        create_resp = client.post("/api/stamps", json={
            "country": "Test", "year": 2000, "description": "To delete",
            "catalog_number": "SG 999", "catalog_type": "SG",
        })
        stamp_id = create_resp.json()["id"]

        response = client.delete(f"/api/stamps/{stamp_id}")
        assert response.status_code == 200

        # Verify deleted
        get_resp = client.get(f"/api/stamps/{stamp_id}")
        assert get_resp.status_code == 404

    def test_collection_stats(self, client):
        response = client.get("/api/stamps/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_stamps" in data
        assert "countries" in data
        assert "total_value" in data


class TestCSVImport:
    """Tests for CSV import functionality."""

    def test_import_csv(self, client):
        csv_content = "country,year,description,catalog_number,catalog_type,denomination,condition,purchase_price,notes\nGreat Britain,1840,Penny Black,SG 1,SG,1d,Used,250.0,First stamp\nFrance,1849,Ceres Issue,SG 1,SG,20c,Mint,150.0,Ceres design"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/api/stamps/import", files=files)
        assert response.status_code == 200
        result = response.json()
        assert result["imported"] == 2

    def test_import_invalid_file(self, client):
        files = {"file": ("test.txt", io.BytesIO(b"not csv"), "text/plain")}
        response = client.post("/api/stamps/import", files=files)
        assert response.status_code == 400

    def test_import_with_errors(self, client):
        csv_content = "country,year,description,catalog_number,catalog_type\nGB,bad_year,Test,SG 1,SG"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/api/stamps/import", files=files)
        assert response.status_code == 200
        result = response.json()
        assert len(result["errors"]) > 0

    def test_search_sort_and_pagination(self, client):
        # Add multiple stamps
        for i in range(5):
            client.post("/api/stamps", json={
                "country": f"Country{i}", "year": 1900 + i,
                "description": f"Stamp {i}", "catalog_number": f"SG {i}",
                "catalog_type": "SG",
            })

        # Test sort by year desc
        response = client.get("/api/stamps", params={"sort_by": "year", "sort_order": "desc"})
        assert response.status_code == 200
        stamps = response.json()["stamps"]
        if len(stamps) >= 2:
            assert stamps[0]["year"] >= stamps[1]["year"]

        # Test pagination
        response = client.get("/api/stamps", params={"page": 1, "per_page": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data["stamps"]) <= 2
        assert data["per_page"] == 2
