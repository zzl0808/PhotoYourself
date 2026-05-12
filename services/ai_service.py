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


import base64
import requests
from PIL import Image
import io


class GLMEvaluator(AIEvaluator):
    """智谱 GLM 视觉模型评估器"""

    API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    MAX_IMAGE_SIZE = 1024  # 最大边长

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GLM_API_KEY")
        if not self.api_key:
            raise ValueError("GLM_API_KEY is required")

    def _load_prompt(self, analysis_data: Dict, prompt_type: str = "portrait") -> str:
        if prompt_type == "portrait":
            from prompts.portrait_photographer_prompt import get_portrait_photographer_prompt
            return get_portrait_photographer_prompt(
                sharpness_score=analysis_data.get("sharpness", 0),
                brightness_val=analysis_data.get("brightness_mean", 0),
                contrast_val=analysis_data.get("brightness_std", 0)
            )
        elif prompt_type == "sharp":
            from prompts.sharp_critic_prompt import get_sharp_critic_prompt
            return get_sharp_critic_prompt(
                sharpness_score=analysis_data.get("sharpness", 0),
                brightness_val=analysis_data.get("brightness_mean", 0),
                contrast_val=analysis_data.get("brightness_std", 0)
            )

    def _compress_image(self, image_path: str) -> bytes:
        """压缩图片，减小体积以适应 API 限制"""
        img = Image.open(image_path)

        max_size = max(img.size)
        if max_size > self.MAX_IMAGE_SIZE:
            ratio = self.MAX_IMAGE_SIZE / max_size
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85, optimize=True)
        return output.getvalue()

    def evaluate(self, image_path: str, analysis_data: Dict, prompt_type: str = "portrait") -> str:
        prompt = self._load_prompt(analysis_data, prompt_type)

        image_bytes = self._compress_image(image_path)
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                    {"type": "text", "text": "请根据以上提示词和图片进行评审。"}
                ]
            }
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "glm-4.6v",
            "messages": messages,
            "stream": False,
            "temperature": 0.8
        }

        response = requests.post(self.API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]


def create_evaluator(model_type: str = "gemini", **kwargs) -> AIEvaluator:
    evaluators = {
        "gemini": GeminiEvaluator,
        "glm": GLMEvaluator,
    }
    if model_type not in evaluators:
        raise ValueError(f"Unknown model type: {model_type}")
    return evaluators[model_type](**kwargs)