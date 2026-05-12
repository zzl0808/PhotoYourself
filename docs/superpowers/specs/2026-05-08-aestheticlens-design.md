# AestheticLens 摄影评估工具 - 设计文档

## 1. 项目概述

**项目名称**: AestheticLens
**类型**: Python Web 应用（Streamlit）
**核心功能**: 上传照片 → EXIF解析 → OpenCV图像分析 → AI审美评价
**目标用户**: 摄影师、摄影爱好者

---

## 2. 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ 文件上传  │  │ EXIF展示  │  │ AI 评价结果展示      │   │
│  └──────────┘  └──────────┘  └──────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ ExifService│ │ CVService │  │ AIEvaluationService │   │
│  └──────────┘  └──────────┘  └──────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                    External APIs                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ PIL/OpenCV│ │ ExifRead  │  │ Gemini API (可替换)  │   │
│  └──────────┘  └──────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 功能模块

### 3.1 文件上传
- 支持拖拽上传（JPEG、PNG、WebP）
- 上传后显示缩略图（最大宽度 600px）
- 支持拍照设备拍摄的照片

### 3.2 EXIF 信息展示
使用 `exifread` 库解析，展示字段：
| 字段 | EXIF Tag |
|------|----------|
| 快门速度 | EXIF ShutterSpeedValue / ExposureTime |
| 光圈 | EXIF ApertureValue / FNumber |
| ISO | EXIF ISOSpeedRatings |
| 焦距 | EXIF FocalLength |
| 拍摄时间 | EXIF DateTimeOriginal |
| 相机型号 | EXIF Model |

### 3.3 OpenCV 图像分析
**清晰度得分（Sharpness Score）**
- 算法: Laplacian Variance
- 原理: 图像边缘越锐利，Laplacian算子响应方差越大
- 范围: 0-100（归一化显示）

**亮度分布（Brightness Distribution）**
- 计算: RGB转YUV，取Y通道均值和方差
- 可视化: 亮度直方图（Streamlit 原生图表）

### 3.4 AI 审美评价（预留接口）
**接口设计**: Strategy Pattern，支持多模型切换
```python
class AIEvaluator(ABC):
    @abstractmethod
    def evaluate(self, image_path: str, analysis_data: dict) -> str:
        pass
```

**默认实现**: Gemini Pro Vision
**System Prompt（专业摄影师视角）**:
```
你是一位拥有20年经验的专业风光与人像摄影师。
你曾获《国家地理》年度最佳摄影奖，擅长捕捉瞬间与构图的完美结合。
你的评价风格：专业、客观、直接指出优点和不足，给出具体改进建议。
评价维度包括：
1. 构图（Composition）- 三分法、引导线、负空间
2. 光线（Lighting）- 光质、光向、曝光准确性
3. 色彩（Color）- 白平衡、色彩情绪、饱和度
4. 情绪（Mood）- 主题表达、故事性
每次评价请给出1-10分的综合美学评分，并详细说明评分理由和改进建议。
```

---

## 4. 目录结构

```
PhotoYourself/
├── app.py                    # Streamlit 主入口
├── services/
│   ├── __init__.py
│   ├── exif_service.py       # EXIF 解析服务
│   ├── cv_service.py         # OpenCV 分析服务
│   └── ai_service.py         # AI 评价服务（策略模式）
├── prompts/
│   └── photographer_prompt.py  # System Prompt
├── requirements.txt
└── docs/
    └── specs/
        └── 2026-05-08-aestheticlens-design.md
```

---

## 5. 依赖

```
streamlit>=1.28
opencv-python>=4.8
exifread>=3.0
pillow>=10.0
google-generativeai>=0.3
plotly>=5.18  # 可选，用于图表
```

---

## 6. 验收标准

- [ ] 支持 JPEG/PNG/WebP 上传并显示缩略图
- [ ] EXIF 信息完整展示（快门、光圈、ISO、焦距）
- [ ] Laplacian 清晰度得分显示
- [ ] 亮度直方图正确渲染
- [ ] AI 评价按钮可触发 Gemini API 调用
- [ ] AI 服务接口可替换（不修改核心代码情况下接入新模型）
