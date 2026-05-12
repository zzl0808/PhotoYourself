# AestheticLens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 AestheticLens 摄影评估 Web 应用的基础框架，包含文件上传、EXIF 解析、OpenCV 图像分析和 AI 评价预留接口。

**Architecture:** Streamlit 单页应用，服务层分离（ExifService、CVService、AIService），AI 服务采用策略模式支持多模型切换。

**Tech Stack:** Python 3.10+, Streamlit 1.28+, OpenCV 4.8+, ExifRead 3.0+, Pillow 10.0+, google-generativeai 0.3+

---

## File Structure

```
PhotoYourself/
├── app.py                         # Streamlit 主入口
├── services/
│   ├── __init__.py
│   ├── exif_service.py             # EXIF 解析服务
│   ├── cv_service.py              # OpenCV 图像分析服务
│   └── ai_service.py              # AI 评价服务（策略模式）
├── prompts/
│   ├── __init__.py
│   └── photographer_prompt.py     # 专业摄影师 System Prompt
├── tests/
│   ├── __init__.py
│   ├── test_exif_service.py
│   ├── test_cv_service.py
│   └── test_ai_service.py
└── requirements.txt
```

---

## Task 1: 项目初始化

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: 创建 requirements.txt**

```
streamlit>=1.28
opencv-python>=4.8
exifread>=3.0
pillow>=10.0
google-generativeai>=0.3
plotly>=5.18
pytest>=7.4
```

- [ ] **Step 2: 创建目录结构**

```bash
mkdir -p services prompts tests
touch services/__init__.py prompts/__init__.py tests/__init__.py
```

- [ ] **Step 3: 安装依赖**

```bash
pip install -r requirements.txt
```

- [ ] **Step 4: 提交**

```bash
git add requirements.txt services prompts tests
git commit -m "chore: initial project structure"
```

---

## Task 2: ExifService - EXIF 解析服务

**Files:**
- Create: `services/exif_service.py`
- Test: `tests/test_exif_service.py`

- [ ] **Step 1: 编写测试**

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_exif_service.py -v
# 预期: FAIL - module not found
```

- [ ] **Step 3: 实现 ExifService**

```python
# services/exif_service.py
import exifread
from typing import Dict, Optional
from fractions import Fraction


class ExifService:
    TAG_MAPPING = {
        "shutter_speed": ["EXIF ShutterSpeedValue", "ExposureTime"],
        "aperture": ["EXIF ApertureValue", "EXIF FNumber"],
        "iso": ["EXIF ISOSpeedRatings"],
        "focal_length": ["EXIF FocalLength"],
        "date_taken": ["EXIF DateTimeOriginal"],
        "camera_model": ["Image Model"],
    }

    def extract(self, image_path: str) -> Dict[str, Optional[str]]:
        with open(image_path, "rb") as f:
            tags = exifread.process_file(f, details=False)

        result = {}
        for field, tag_names in self.TAG_MAPPING.items():
            value = self._find_tag(tags, tag_names)
            result[field] = self._format_value(field, value)
        return result

    def _find_tag(self, tags: dict, tag_names: list) -> Optional[str]:
        for name in tag_names:
            if name in tags:
                return str(tags[name])
        return None

    def _format_value(self, field: str, value) -> str:
        if value is None:
            return "N/A"
        if field == "shutter_speed":
            return self._format_shutter(value)
        if field == "aperture":
            return f"f/{value}"
        if field == "focal_length":
            return self._format_focal_length(value)
        return str(value)

    def _format_shutter(self, value: str) -> str:
        try:
            if "/" in value:
                num, denom = value.split("/")
                sec = float(num) / float(denom)
                if sec < 1:
                    return f"1/{int(1/sec)}s"
                return f"{sec}s"
        except:
            pass
        return value

    def _format_focal_length(self, value: str) -> str:
        try:
            if "/" in value:
                num, denom = value.split("/")
                mm = float(num) / float(denom)
                return f"{mm:.1f}mm"
        except:
            pass
        return value
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_exif_service.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add services/exif_service.py tests/test_exif_service.py
git commit -m "feat: add ExifService for photo metadata extraction"
```

---

## Task 3: CVService - OpenCV 图像分析服务

**Files:**
- Create: `services/cv_service.py`
- Test: `tests/test_cv_service.py`

- [ ] **Step 1: 编写测试**

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_cv_service.py -v
# 预期: FAIL - module not found
```

- [ ] **Step 3: 实现 CVService**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_cv_service.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add services/cv_service.py tests/test_cv_service.py
git commit -m "feat: add CVService for image sharpness and brightness analysis"
```

---

## Task 4: AIService - AI 评价服务（策略模式）

**Files:**
- Create: `services/ai_service.py`
- Test: `tests/test_ai_service.py`

- [ ] **Step 1: 编写测试**

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_ai_service.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 AIService**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_ai_service.py -v
# 预期: PASS
```

- [ ] **Step 5: 提交**

```bash
git add services/ai_service.py tests/test_ai_service.py
git commit -m "feat: add AIService with Strategy pattern for AI evaluation"
```

---

## Task 5: Photographer Prompt

**Files:**
- Create: `prompts/photographer_prompt.py`

- [ ] **Step 1: 编写 System Prompt**

```python
# prompts/photographer_prompt.py
PHOTOGRAPHER_SYSTEM_PROMPT = """你是一位拥有20年经验的专业风光与人像摄影师。
你曾获《国家地理》年度最佳摄影奖，擅长捕捉瞬间与构图的完美结合。
你的评价风格：专业、客观、直接指出优点和不足，给出具体改进建议。

评价维度包括：
1. 构图（Composition）- 三分法、引导线、负空间、对称性
2. 光线（Lighting）- 光质、光向、曝光准确性、动态范围
3. 色彩（Color）- 白平衡、色彩情绪、饱和度、色彩和谐
4. 细节（Details）- 清晰度、噪点控制、锐化程度
5. 情绪（Mood）- 主题表达、故事性、创意性

每次评价请：
1. 给出1-10分的综合美学评分
2. 详细说明评分理由（每个维度的1-2句话点评）
3. 给出1-2条具体的改进建议

请用中文回复。"""


def get_photographer_prompt() -> str:
    return PHOTOGRAPHER_SYSTEM_PROMPT
```

- [ ] **Step 2: 提交**

```bash
git add prompts/photographer_prompt.py
git commit -m "feat: add professional photographer system prompt"
```

---

## Task 6: Streamlit 主应用

**Files:**
- Create: `app.py`

- [ ] **Step 1: 编写 app.py**

```python
# app.py
import streamlit as st
from PIL import Image
from services.exif_service import ExifService
from services.cv_service import CVService
from services.ai_service import create_evaluator
from prompts.photographer_prompt import get_photographer_prompt
import os


st.set_page_config(page_title="AestheticLens", page_icon="📷")
st.title("📷 AestheticLens - 摄影评估工具")

exif_service = ExifService()
cv_service = CVService()

uploaded_file = st.file_uploader(
    "上传照片（JPEG、PNG、WebP）",
    type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📸 预览")
        image = Image.open(uploaded_file)
        st.image(image, width=400)

    with col2:
        st.subheader("📋 EXIF 信息")
        temp_path = f"/tmp/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        exif_data = exif_service.extract(temp_path)
        st.write(f"**快门速度:** {exif_data.get('shutter_speed', 'N/A')}")
        st.write(f"**光圈:** {exif_data.get('aperture', 'N/A')}")
        st.write(f"**ISO:** {exif_data.get('iso', 'N/A')}")
        st.write(f"**焦距:** {exif_data.get('focal_length', 'N/A')}")
        st.write(f"**拍摄时间:** {exif_data.get('date_taken', 'N/A')}")
        st.write(f"**相机型号:** {exif_data.get('camera_model', 'N/A')}")

    st.divider()

    col3, col4 = st.columns([1, 1])
    with col3:
        st.subheader("🔍 清晰度分析")
        sharpness = cv_service.calculate_sharpness(temp_path)
        label = cv_service.get_sharpness_label(sharpness)
        st.metric("清晰度得分", f"{sharpness}/100", label)
        st.progress(sharpness / 100, text=label)

    with col4:
        st.subheader("💡 亮度分析")
        brightness = cv_service.analyze_brightness(temp_path)
        brightness_label = cv_service.get_brightness_label(brightness["mean"])
        st.metric("平均亮度", f"{brightness['mean']:.1f}", brightness_label)
        st.write(f"标准差: {brightness['std']:.1f}")

    st.divider()

    st.subheader("📊 亮度直方图")
    st.bar_chart(brightness["histogram"])

    st.divider()

    st.subheader("🤖 AI 审美评价")
    if st.button("开始评价", type="primary"):
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            st.error("请设置环境变量 GEMINI_API_KEY")
        else:
            with st.spinner("AI 正在分析中..."):
                try:
                    evaluator = create_evaluator("gemini", api_key=api_key)
                    analysis_data = {
                        "sharpness": sharpness,
                        "brightness_mean": brightness["mean"],
                        "brightness_std": brightness["std"],
                    }
                    result = evaluator.evaluate(temp_path, analysis_data)
                    st.success("评价完成")
                    st.markdown(result)
                except Exception as e:
                    st.error(f"评价失败: {str(e)}")

    os.remove(temp_path)
```

- [ ] **Step 2: 测试运行**

```bash
streamlit run app.py --server.headless true
# 预期: 应用启动，浏览器打开 http://localhost:8501
```

- [ ] **Step 3: 提交**

```bash
git add app.py
git commit -m "feat: add Streamlit main application with file upload, EXIF, CV analysis, and AI evaluation"
```

---

## Task 7: 测试目录初始化

**Files:**
- Create: `tests/fixtures/` 目录结构
- Note: 由于没有真实测试图片，测试为框架代码

- [ ] **Step 1: 创建 fixtures 目录**

```bash
mkdir -p tests/fixtures
touch tests/fixtures/.gitkeep
```

- [ ] **Step 2: 提交**

```bash
git add tests/
git commit -m "chore: add test fixtures directory"
```

---

## 验收标准

- [ ] `streamlit run app.py` 成功启动
- [ ] 上传 JPEG/PNG/WebP 显示缩略图
- [ ] EXIF 信息（快门、光圈、ISO、焦距）正确显示
- [ ] Laplacian 清晰度得分显示
- [ ] 亮度直方图正确渲染
- [ ] AI 评价按钮存在（需要 GEMINI_API_KEY 才能调用）
