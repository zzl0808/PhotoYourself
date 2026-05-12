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

    def evaluate_histogram(self, brightness_data: Dict) -> str:
        """对亮度直方图进行专业评价"""
        mean = brightness_data["mean"]
        std = brightness_data["std"]
        histogram = brightness_data["histogram"]

        # 计算暗部、亮部、中间调占比
        dark = sum(histogram[:64])      # 0-63 暗部
        mid = sum(histogram[64:192])    # 64-191 中间调
        bright = sum(histogram[192:])   # 192-255 亮部
        total = sum(histogram) or 1

        dark_ratio = dark / total * 100
        mid_ratio = mid / total * 100
        bright_ratio = bright / total * 100

        # 检查是否有截断（曝光过度/不足）
        left_clip = histogram[0] > 50   # 左侧截断
        right_clip = histogram[255] > 50  # 右侧截断

        comments = []

        # 整体亮度评价
        if left_clip:
            comments.append("⚠️ 存在暗部截断，画面暗部细节丢失")
        elif right_clip:
            comments.append("⚠️ 存在亮部截断，画面高光过曝")
        elif mean < 50:
            comments.append("📉 整体曝光不足，画面偏暗，细节难以辨认")
        elif mean < 70:
            comments.append("📉 画面偏暗，建议适当增加曝光")
        elif mean > 200:
            comments.append("📗 整体曝光过度，画面泛白，高光细节丢失")
        elif mean > 180:
            comments.append("📗 画面偏亮，细节可能被高光淹没")
        elif 100 <= mean <= 160:
            comments.append("✅ 曝光正常，亮度分布合理")

        # 对比度评价
        if std < 20:
            comments.append("⚠️ 对比度偏低，画面灰蒙蒙，缺乏层次感")
        elif std > 80:
            comments.append("⚠️ 对比度过高，画面明暗反差过大")
        elif std > 50:
            comments.append("✅ 对比度适中，画面层次分明")

        # 直方图分布评价
        if dark_ratio > 40 and mid_ratio < 40:
            comments.append("📊 直方图偏左分布，属于低调影像，适合表达沉稳神秘氛围")
        elif bright_ratio > 40 and mid_ratio < 40:
            comments.append("📊 直方图偏右分布，属于高调影像，适合表达明亮欢快氛围")
        elif 45 < mid_ratio < 70:
            comments.append("📊 中间调丰富，过渡平滑，影调自然")

        return " ".join(comments) if comments else "📊 直方图分布正常"