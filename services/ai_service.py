# services/ai_service.py
from abc import ABC, abstractmethod
from typing import Dict
import os


class AIEvaluator(ABC):
    @abstractmethod
    def evaluate(self, image_path: str, analysis_data: Dict) -> str:
        pass

    def _load_prompt(self) -> str:
        from prompts.photographer_prompt import get_photographer_prompt
        return get_photographer_prompt()


class GeminiEvaluator(AIEvaluator):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")

    def evaluate(self, image_path: str, analysis_data: Dict) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)

        model = genai.GenerativeModel("gemini-pro-vision")
        prompt = self._load_prompt()

        with open(image_path, "rb") as f:
            image_data = f.read()

        response = model.generate_content([
            prompt,
            {"image": image_data}
        ])
        return response.text


def create_evaluator(model_type: str = "gemini", **kwargs) -> AIEvaluator:
    evaluators = {
        "gemini": GeminiEvaluator,
    }
    if model_type not in evaluators:
        raise ValueError(f"Unknown model type: {model_type}")
    return evaluators[model_type](**kwargs)