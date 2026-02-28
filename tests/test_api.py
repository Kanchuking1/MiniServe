"""
API tests for FastAPI app: /, /health, /predict.
Uses TestClient; app startup loads the model once per module.
"""

import io

import pytest
from fastapi.testclient import TestClient

# Import app after path is set (conftest adds repo root)
from api.main import app


@pytest.fixture(scope="module")
def client():
    """TestClient with app; use as context manager so lifespan (startup) runs and app.state.model is set."""
    with TestClient(app) as c:
        yield c


class TestRoot:
    def test_root_returns_service_info(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["service"] == "MiniServe"
        assert "endpoints" in data
        assert "/predict" in data["endpoints"]
        assert "/health" in data["endpoints"]


class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestPredict:
    def test_predict_accepts_image_returns_prediction(self, client, sample_image):
        buf = io.BytesIO()
        sample_image.save(buf, format="PNG")
        buf.seek(0)
        r = client.post("/predict", files={"file": ("image.png", buf, "image/png")})
        assert r.status_code == 200
        data = r.json()
        assert "class_id" in data
        assert "label" in data
        assert "confidence" in data
        assert isinstance(data["class_id"], int)
        assert 0 <= data["class_id"] <= 999
        assert 0 <= data["confidence"] <= 1

    def test_predict_rejects_non_image(self, client):
        r = client.post(
            "/predict",
            files={"file": ("file.txt", io.BytesIO(b"not an image"), "text/plain")},
        )
        assert r.status_code == 400
        assert "Expected an image" in r.json()["detail"]

    def test_predict_rejects_invalid_image_bytes(self, client):
        r = client.post(
            "/predict",
            files={"file": ("x.png", io.BytesIO(b"not png content"), "image/png")},
        )
        assert r.status_code == 400
        assert "Invalid image" in r.json()["detail"]
