# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
streamlit run app.py --server.headless true
```

## Architecture

**AestheticLens** - A Streamlit photo evaluation app with three analysis layers and AI evaluation.

### Services Layer
- `services/exif_service.py` - EXIF metadata extraction using exifread
- `services/cv_service.py` - OpenCV image analysis (sharpness via Laplacian variance, brightness histogram)
- `services/ai_service.py` - AI evaluation with Strategy pattern

### AI Strategy Pattern
- `AIEvaluator` is the abstract base class
- `GeminiEvaluator` - uses Google Gemini Pro Vision API
- `GLMEvaluator` - uses Zhipu GLM-4.6v API with base64-encoded images, image compressed to 1024px max

### Prompt System
Prompts are stored as `.md` files in `prompts/` with template variables (`{sharpness_score}`, `{brightness_val}`, `{contrast_val}`).

Two evaluation modes:
- `portrait` - professional photographer style (portrait_photographer.md)
- `sharp` - 贴吧-style critical review (sharp_critic.md)

### Environment Variables
- `GLM_API_KEY` - Zhipu API key (primary)
- `GEMINI_API_KEY` - Google API key

### Key Implementation Details
- `set_page_config()` must be the first Streamlit command
- GLM evaluator accepts `prompt_type` parameter to switch between evaluation styles
- All image analysis uses temp files at `/tmp/`
- Chinese font path: `/System/Library/Fonts/Hiragino Sans GB.ttc`