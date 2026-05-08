# tests/test_ai_service.py
import pytest
from services.ai_service import AIEvaluator, GeminiEvaluator, create_evaluator

def test_evaluator_interface():
    evaluator = GeminiEvaluator(api_key="test_key")
    assert hasattr(evaluator, "evaluate")
    assert callable(evaluator.evaluate)

def test_create_evaluator_returns_correct_type():
    evaluator = create_evaluator("gemini", api_key="test")
    assert isinstance(evaluator, GeminiEvaluator)

def test_create_evaluator_raises_for_unknown():
    with pytest.raises(ValueError):
        create_evaluator("unknown_model", api_key="test")