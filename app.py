# app.py
import streamlit as st
from PIL import Image
from datetime import datetime
from services.exif_service import ExifService
from services.cv_service import CVService
from services.ai_service import create_evaluator
import os
import re
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="AestheticLens", page_icon="📷", layout="wide")

# ===== 全局样式注入 =====
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
.block-container {padding-top: 1.5rem; padding-bottom: 1.5rem; padding-left: 2rem; padding-right: 2rem;}
[data-testid="stAppViewContainer"] {background: #F5F5F5;}
.stButton > button {border-radius: 8px;}
.img-card {border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.08);}
.exif-line {font-size: 13px; color: #666; letter-spacing: 0.3px; margin-top: 8px;}
.metric-card {background: white; border-radius: 10px; padding: 14px; border: 1px solid #E0E0E0; text-align: center;}
.metric-val {font-size: 26px; font-weight: 700; color: #1A1A1A;}
.metric-label {font-size: 11px; color: #888; margin-top: 2px;}
.metric-sub {font-size: 10px; color: #AAA;}
.stMetric {background: white; border-radius: 8px; padding: 8px;}
</style>
""", unsafe_allow_html=True)
st.title("📷 AestheticLens")

exif_service = ExifService()
cv_service = CVService()

uploaded_file = st.file_uploader(
    "拖拽或点击上传照片（支持 JPEG、PNG、WebP）",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed"
)

if uploaded_file:
    temp_path = f"/tmp/{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    exif_data = exif_service.extract(temp_path)
    sharpness = cv_service.calculate_sharpness(temp_path)
    sharpness_label = cv_service.get_sharpness_label(sharpness)
    brightness = cv_service.analyze_brightness(temp_path)
    brightness_label = cv_service.get_brightness_label(brightness["mean"])
    histogram_evaluation = cv_service.evaluate_histogram(brightness)

    # ===== 左右两栏 =====
    col1, col2 = st.columns([4, 6])

    with col1:
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True, clamp=True)

        # 紧凑 EXIF 单行
        camera = exif_data.get('camera_model', 'N/A')
        shutter = exif_data.get('shutter_speed', 'N/A')
        aperture = exif_data.get('aperture', 'N/A')
        iso = exif_data.get('iso', 'N/A')
        focal = exif_data.get('focal_length', 'N/A')
        date = exif_data.get('date_taken', 'N/A')

        parts = []
        if camera != 'N/A': parts.append(f"📷 {camera}")
        if aperture != 'N/A': parts.append(f"🔘 {aperture}")
        if shutter != 'N/A': parts.append(f"⏱️ {shutter}")
        if iso != 'N/A': parts.append(f"🎞️ ISO {iso}")
        if focal != 'N/A': parts.append(f"🔍 {focal}")

        exif_str = " | ".join(parts) if parts else "无 EXIF 信息"
        st.markdown(f"<p class='exif-line'>{exif_str}</p>", unsafe_allow_html=True)

        if date != 'N/A':
            st.markdown(f"<p class='exif-line' style='color:#999'>📅 {date}</p>", unsafe_allow_html=True)

    with col2:
        # ===== 技术指标卡片 =====
        with st.container(border=True):
            m1, m2, m3 = st.columns(3)

            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{sharpness}</div>
                    <div class="metric-label">清晰度</div>
                    <div class="metric-sub">{sharpness_label}</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(sharpness / 100)

            with m2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{brightness['mean']:.0f}</div>
                    <div class="metric-label">亮度均值</div>
                    <div class="metric-sub">{brightness_label}</div>
                </div>
                """, unsafe_allow_html=True)

            with m3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{brightness['std']:.0f}</div>
                    <div class="metric-label">对比度</div>
                    <div class="metric-sub">标准差</div>
                </div>
                """, unsafe_allow_html=True)

        # ===== 直方图折叠 =====
        with st.expander("📊 查看详细光影分布"):
            st.markdown(f"**光影评价：** {histogram_evaluation}")
            import pandas as pd
            hist_df = pd.DataFrame({"分布": brightness["histogram"]})
            st.bar_chart(hist_df, height=160)

        # ===== AI 评价区 =====
        st.subheader("🤖 AI 审美评价")

        c1, c2 = st.columns([1, 4])
        with c1:
            model_options = ["glm", "gemini"]
            selected_model = st.selectbox("模型", model_options, index=0, label_visibility="collapsed")
        with c2:
            api_key_env = f"{selected_model.upper()}_API_KEY"
            api_key = os.environ.get(api_key_env, "")
            if not api_key:
                st.warning(f"请设置 {api_key_env}")

        style_options = ["专业评价", "锐评"]
        selected_style = st.selectbox("评价风格", style_options, index=0)
        style_map = {"专业评价": "portrait", "锐评": "sharp"}
        prompt_type = style_map[selected_style]

        if st.button("🎨 开始评价", type="primary", use_container_width=True, disabled=not api_key):
            with st.spinner("AI 分析中..."):
                try:
                    evaluator = create_evaluator(selected_model, api_key=api_key)
                    analysis_data = {
                        "sharpness": sharpness,
                        "brightness_mean": brightness["mean"],
                        "brightness_std": brightness["std"],
                    }
                    ai_result = evaluator.evaluate(temp_path, analysis_data, prompt_type=prompt_type)
                    st.session_state["ai_result"] = ai_result
                    st.session_state["ai_model"] = selected_model
                except Exception as e:
                    st.error(f"评价失败: {str(e)}")

        # ===== AI 结果展示 =====
        if "ai_result" in st.session_state:
            result = st.session_state["ai_result"]

            # 评分卡片（兼容 portrait 和 sharp 格式）
            score_match = re.search(r'\d+\.?\d*', result)
            score_val = score_match.group() if score_match else "N/A"
            st.success(f"🏆 综合审美得分：**{score_val}/100**")

            # 解析并格式化各段落
            lines = result.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Emoji 开头的标题加粗
                if any(line.startswith(e) for e in ['🏆', '🖼️', '🔍', '🛠️', '📝']):
                    parts = line.split('：', 1)
                    if len(parts) == 2:
                        st.markdown(f"**{parts[0]}：**{parts[1]}")
                    else:
                        st.markdown(f"**{line}**")
                elif line.startswith('>'):
                    st.markdown(line)
                else:
                    st.markdown(line)

            st.caption(f"⏱ 评估时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} · 模型：{st.session_state.get('ai_model', selected_model)}")

        # ===== 海报导出 =====
        st.divider()
        import io
        import textwrap
        import re
        from PIL import Image, ImageDraw, ImageFont

        # === 画布基础 ===
        poster_w, poster_h = 1080, 1920
        bg_color = "#FAF9F6"
        poster = Image.new("RGB", (poster_w, poster_h), bg_color)
        draw = ImageDraw.Draw(poster)

        # === 字体配置 ===
        font_path = "/System/Library/Fonts/Hiragino Sans GB.ttc"
        try:
            font_title = ImageFont.truetype(font_path, 72)   # 大标题
            font_sec   = ImageFont.truetype(font_path, 38)   # 章节标题
            font_param = ImageFont.truetype(font_path, 30)   # 参数标签
            font_body  = ImageFont.truetype(font_path, 26)   # 正文段落
            font_score = ImageFont.truetype(font_path, 96)   # 分数大字
        except:
            font_title = font_sec = font_param = font_body = font_score = ImageFont.load_default()

        # === 工具函数 ===
        def filter_emoji(text: str) -> str:
            """去除 Emoji，避免 Pillow 渲染乱码"""
            return re.sub(r'[\U00010000-\U0010ffff]', '', text)

        def rounded_rect(draw, xy, radius, fill):
            """绘制圆角矩形"""
            x0, y0, x1, y1 = xy
            r = radius
            draw.rectangle([x0+r, y0, x1-r, y1], fill=fill)
            draw.rectangle([x0, y0+r, x1, y1-r], fill=fill)
            draw.pieslice([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=fill)
            draw.pieslice([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=fill)
            draw.pieslice([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=fill)
            draw.pieslice([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=fill)

        def wrap_text(text, width=38):
            return textwrap.wrap(text, width=width)

        # === 顶部照片区 ===
        margin = 60
        photo_area_h = poster_h * 0.45
        img_disp = image.copy()
        img_disp.thumbnail((poster_w - margin * 2, int(photo_area_h) - margin), Image.LANCZOS)
        photo_x = (poster_w - img_disp.width) // 2
        photo_y = margin
        # 圆角遮罩（白色边框）
        rounded_rect(draw, [photo_x - 8, photo_y - 8, photo_x + img_disp.width + 8, photo_y + img_disp.height + 8], 16, "#FFFFFF")
        poster.paste(img_disp, (photo_x, photo_y))

        # === 中间深色数据卡片 ===
        card_y = photo_y + img_disp.height + 40
        card_h = 280
        card_padding = 50
        rounded_rect(draw, [margin, card_y, poster_w - margin, card_y + card_h], 20, "#2B2D42")

        y = card_y + card_padding
        draw.text((margin + card_padding, y), "相机参数", fill="#8D99AE", font=font_param)
        y += 50
        params_line1 = f"快门  {shutter}   光圈  {aperture}   ISO  {iso}"
        draw.text((margin + card_padding, y), params_line1, fill="#EDF2F4", font=font_body)
        y += 44
        params_line2 = f"焦距  {focal}   相机  {camera}"
        draw.text((margin + card_padding, y), params_line2, fill="#EDF2F4", font=font_body)
        y += 60

        draw.text((margin + card_padding, y), "技术指标", fill="#8D99AE", font=font_param)
        y += 50
        draw.text((margin + card_padding, y), f"清晰度  {sharpness}/100  ({sharpness_label})", fill="#EDF2F4", font=font_body)
        y += 44
        # 进度条
        bar_x = margin + card_padding
        bar_y = y
        bar_w = poster_w - margin * 2 - card_padding * 2
        bar_h = 18
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill="#3D5A80")
        draw.rectangle([bar_x, bar_y, bar_x + int(bar_w * sharpness / 100), bar_y + bar_h], fill="#98C1D9")
        y += 36
        draw.text((margin + card_padding, y), f"亮度  {brightness['mean']:.0f}  ({brightness_label})   对比度  {brightness['std']:.0f}", fill="#EDF2F4", font=font_body)

        # === 底部 AI 评价区 ===
        ai_start_y = card_y + card_h + 50

        # 综合审美得分（单独大字强调）
        score_color = "#E63946"
        score_text = "N/A"
        if "ai_result" in st.session_state:
            m = re.search(r'(\d+\.?\d*)\/100', st.session_state["ai_result"])
            if m:
                score_text = m.group(1)
        draw.text((margin, ai_start_y), f"🏆 {score_text}", fill=score_color, font=font_score)
        draw.text((margin, ai_start_y + font_score.size + 10), "/100", fill="#CCCCCC", font=font_sec)

        y = ai_start_y + 130

        if "ai_result" in st.session_state:
            ai_text = filter_emoji(st.session_state["ai_result"])
            # 按行处理，提取标题和内容
            for line in ai_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # 标题行（如 🖼️ 题材识别）
                if any(line.startswith(e) for e in ['🏆', '🖼️', '🔍', '🛠️', '📝', '评分', '题材', '视觉', '细节', '进阶', '灵感', '综合']) and '：' in line:
                    parts = line.split('：', 1)
                    draw.text((margin, y), f"• {parts[0]}：", fill="#2B2D42", font=font_sec)
                    y += font_sec.size + 20
                    if len(parts) > 1:
                        for w in wrap_text(parts[1], width=36):
                            draw.text((margin + 30, y), w, fill="#555555", font=font_body, spacing=12)
                            y += font_body.size + 28
                else:
                    for w in wrap_text(line, width=36):
                        draw.text((margin, y), w, fill="#555555", font=font_body, spacing=12)
                        y += font_body.size + 28
                if y > poster_h - 150:
                    break
        else:
            draw.text((margin, y), "• AI 评价暂不可用", fill="#AAAAAA", font=font_body, spacing=12)
            y += font_body.size + 28
            draw.text((margin + 30, y), "点击「开始评价」生成 AI 审美评价", fill="#CCCCCC", font=font_body, spacing=12)

        # === 底部水印 ===
        draw.rectangle([0, poster_h - 80, poster_w, poster_h], "#2B2D42")
        draw.text((margin, poster_h - 60), "AestheticLens", fill="#8D99AE", font=font_sec)
        draw.text((poster_w - 250, poster_h - 60), datetime.now().strftime('%Y.%m.%d'), fill="#555555", font=font_body)

        # === 导出 ===
        buffer = io.BytesIO()
        poster.save(buffer, format="PNG")
        buffer.seek(0)
        st.download_button(
            label="📥 导出海报 PNG",
            data=buffer.getvalue(),
            file_name=f"AestheticLens_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
            mime="image/png",
            use_container_width=True
        )

    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)