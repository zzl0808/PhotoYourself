# tests/test_cv_service.py
import pytest
import numpy as np
from services.cv_service import CVService

@pytest.fixture
def sample_image_path():
    return "tests/fixtures/test_photo.jpg"

def test_sharpness_score_range(sample_image_path):
    service = CVService()
    score = service.calculate_sharpness(sample_image_path)
    assert 0 <= score <= 100

def test_brightness_data_structure(sample_image_path):
    service = CVService()
    result = service.analyze_brightness(sample_image_path)
    assert "mean" in result
    assert "std" in result
    assert "histogram" in result
    assert len(result["histogram"]) == 256

def test_blur_detection_label(sample_image_path):
    service = CVService()
    score = service.calculate_sharpness(sample_image_path)
    label = service.get_sharpness_label(score)
    assert label in ["模糊", "一般", "清晰", "非常清晰"]