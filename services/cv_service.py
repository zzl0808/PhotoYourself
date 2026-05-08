# services/cv_service.py
import cv2
import numpy as np
from typing import Dict, Tuple


class CVService:
    SHARPNESS_WEIGHT = 1000.0  # 归一化权重

    def calculate_sharpness(self, image_path: str) -> float:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        score = min(variance / self.SHARPNESS_WEIGHT * 100, 100)
        return round(score, 2)

    def get_sharpness_label(self, score: float) -> str:
        if score < 10:
            return "模糊"
        elif score < 30:
            return "一般"
        elif score < 60:
            return "清晰"
        else:
            return "非常清晰"

    def analyze_brightness(self, image_path: str) -> Dict:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
        y_channel = yuv[:, :, 0]
        hist = cv2.calcHist([y_channel], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()
        return {
            "mean": round(float(y_channel.mean()), 2),
            "std": round(float(y_channel.std()), 2),
            "histogram": [int(h) for h in hist * 1000]
        }

    def get_brightness_label(self, mean: float) -> str:
        if mean < 60:
            return "偏暗"
        elif mean < 150:
            return "正常"
        else:
            return "过亮"