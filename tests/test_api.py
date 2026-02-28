"""
API tests for FastAPI app: /, /health, /submit, /result/{job_id}.
Day 3: async submission (no in-process inference).
"""

import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Import app after path is set (conftest adds repo root)
from api.main import app


@pytest.fixture(scope="module")
def client():
    """TestClient with app; startup runs once per module."""
    with TestClient(app) as c:
        yield c


class TestRoot:
    def test_root_returns_service_info(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["service"] == "MiniServe"
        assert "endpoints" in data
        assert "/submit" in data["endpoints"]
        assert "/result/{job_id}" in data["endpoints"]
        assert "/health" in data["endpoints"]


class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestSubmit:
    @patch("api.main.push_job")
    def test_submit_accepts_image_returns_job_id(self, mock_push_job, client, sample_image):
        mock_push_job.return_value = "0-1"
        buf = io.BytesIO()
        sample_image.save(buf, format="PNG")
        buf.seek(0)
        r = client.post("/submit", files={"file": ("image.png", buf, "image/png")})
        assert r.status_code == 200
        data = r.json()
        assert "job_id" in data
        assert len(data["job_id"]) == 36  # uuid4 hex + dashes
        mock_push_job.assert_called_once()

    def test_submit_rejects_non_image(self, client):
        r = client.post(
            "/submit",
            files={"file": ("file.txt", io.BytesIO(b"not an image"), "text/plain")},
        )
        assert r.status_code == 400
        assert "Expected an image" in r.json()["detail"]

    def test_submit_rejects_empty_file(self, client):
        r = client.post(
            "/submit",
            files={"file": ("empty.png", io.BytesIO(), "image/png")},
        )
        assert r.status_code == 400
        assert "Empty" in r.json()["detail"]


class TestResult:
    @patch("api.main.get_result")
    def test_result_unknown_job_returns_pending(self, mock_get_result, client):
        mock_get_result.return_value = None
        r = client.get("/result/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 200
        assert r.json() == {"status": "pending"}
