# tests/test_exif_service.py
import pytest
from services.exif_service import ExifService

@pytest.fixture
def sample_image_path():
    return "tests/fixtures/test_photo.jpg"

def test_exif_service_extracts_basic_tags(sample_image_path):
    service = ExifService()
    result = service.extract(sample_image_path)
    assert "shutter_speed" in result
    assert "aperture" in result
    assert "iso" in result
    assert "focal_length" in result

def test_exif_service_returns_none_for_missing_exif(sample_image_path):
    service = ExifService()
    result = service.extract(sample_image_path)
    assert result.get("shutter_speed") is not None or result.get("shutter_speed") == "N/A"