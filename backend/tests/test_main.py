import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app
from backend.gemini_service import validate_gemini_payload
from backend.models import FloorPlan

client = TestClient(app)

PAYLOAD = {"image": {"width": 10, "height": 10}, "walls": [{"id": "wall-1", "start": {"x": 0, "y": 0}, "end": {"x": 1, "y": 0}, "thickness": .01, "confidence": .9}], "windows": [{"id": "window-1", "start": {"x": .2, "y": 0}, "end": {"x": .3, "y": 0}, "wallId": "wall-1", "confidence": .8}]}


def upload(content=b"image", content_type="image/png"):
    return client.post("/api/floor-plans/parse", files={"file": ("plan.png", content, content_type)})


def test_rejects_unsupported_upload():
    assert upload(content_type="application/pdf").status_code == 415


def test_returns_mocked_parse(monkeypatch):
    monkeypatch.setattr("backend.main.settings.gemini_api_key", "test-key")
    with patch("backend.main.parse_floor_plan", return_value=FloorPlan.model_validate(PAYLOAD)):
        response = upload()
    assert response.status_code == 200
    assert response.json()["walls"][0]["id"] == "wall-1"


def test_returns_safe_error_for_gemini_failure(monkeypatch):
    monkeypatch.setattr("backend.main.settings.gemini_api_key", "test-key")
    with patch("backend.main.parse_floor_plan", side_effect=Exception("secret detail")):
        response = upload()
    assert response.status_code == 502


def test_rejects_invalid_gemini_json():
    with pytest.raises(Exception):
        FloorPlan.model_validate_json("{not valid json")


def test_adds_trusted_image_metadata_before_validating_geometry():
    result = validate_gemini_payload({"walls": PAYLOAD["walls"], "windows": PAYLOAD["windows"]}, 1920, 1080)
    assert result.image.width == 1920
    assert result.image.height == 1080
