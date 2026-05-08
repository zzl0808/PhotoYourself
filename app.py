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