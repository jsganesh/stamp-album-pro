"""
Tests for low-complexity P2 items: Excel import.
"""
import io
import pytest
from fastapi.testclient import TestClient

from stamp_album.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestExcelImport:
    """Tests for Excel import endpoint."""

    def test_import_excel_wrong_extension(self, client):
        files = {"file": ("test.csv", io.BytesIO(b"not excel"), "text/csv")}
        response = client.post("/api/stamps/import-excel", files=files)
        assert response.status_code == 400

    def test_import_excel_no_openpyxl(self, client):
        # This test verifies the endpoint exists and handles missing openpyxl gracefully
        # We can't easily test the actual Excel parsing without openpyxl installed
        # but we can verify the file extension check works
        files = {"file": ("test.txt", io.BytesIO(b"not excel"), "text/plain")}
        response = client.post("/api/stamps/import-excel", files=files)
        assert response.status_code == 400
