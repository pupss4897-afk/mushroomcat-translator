import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import json
import re
import traceback
from PIL import Image

# ==========================================
# 1. 網頁設定
# ==========================================
st.set_page_config(page_title="香菇爸的貓咪全方位管家", page_icon="🍄", layout="wide")

# ==========================================
# 2. 側邊欄
# ==========================================
st.sidebar.title("🍄 關於香菇爸")
st.sidebar.info("嗨！我是香菇爸，專精於貓科動物行為與營養分析。")

YOUR_CHANNEL_LINK = "https://www.instagram.com/love_mushroom55?igsh=NTl4bmg2djJyejFn&utm_source=qr" 
YOUR_LINE_LINK = "https://s.luckycat.no8.io/link/channels/ZIGreweSIw"

st.sidebar.markdown("### 📢 追蹤更多")
st.sidebar.link_button("📺 前往香菇爸的頻道", YOUR_CHANNEL_LINK, use_container_width=True)
st.sidebar.link_button("🎁 加 LINE 領取「貓咪懶人包」", YOUR_LINE_LINK, type="primary", use_container_width=True)

st.sidebar.markdown("---")

app_mode = st.sidebar.radio(
    "請選擇功能：",
    ["🐱 貓咪讀心術 (影片)", "🥫 飼料罐頭分析 (照片)", "📊 熱量&喝水計算機"]
)

st.sidebar.markdown("---")
st.sidebar.title("⚙️ 設定")

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    default_key = ""
    st.sidebar.warning("⚠️ 目前是「本機開發模式」，請手動輸入 Key")
    api_key = st.sidebar.text_input("輸入 Google API Key", value=default_key, type="password")

# ==========================================
# 工具函數
# ==========================================
def clean_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE)
    return text.strip()

CANDIDATE_MODELS = [
    "gemini-1.5-flash",          
    "gemini-1.5-flash-001",
    "gemini-1.5-pro",            
    "gemini-2.0-flash",
    "gemini-flash-latest"
]

# ==========================================
# 功能 A: 影片分析
# ==========================================
def analyze_video(api_key, video_path, mime_type):
    genai.configure(api_key=api_key)
    prompt = """
    角色: 香菇爸 (資深動物行為學家與貓咪溝通師)。
    任務: 分析貓咪影片的視覺與聽覺，解讀情緒與特徵。
    輸出格式: JSON。
    欄位: mood, intimacy_score, translation, reasoning, suggestion, chonk_score, chonk_comment, cat_mbti, hashtags.
    翻譯風格: 生動有趣、甚至有點傲嬌。
    """
    with st.spinner('🍄 香菇爸正在解讀主子心聲...'):
        try:
            video_file = genai.upload_file(path=video_path, mime_type=mime_type)
        except Exception as e:
            st.error(f"上傳失敗: {e}")
            return None
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)
        if video_file.state.name == "FAILED":
            st.error("❌ 影片處理失敗。")
            return None
        for model_name in CANDIDATE_MODELS:
            try:
                model = genai.GenerativeModel(model_name=model_name, generation_config={"response_mime_type": "application/json"})
                response = model.generate_content([video_file, prompt])
                try: genai.delete_file(video_file.name)
                except: pass
                return json.loads(clean_json_response(response.text))
            except: continue
        st.error("AI 忙碌中，請稍後再試。")
        return None

# ==========================================
# 功能 B: 圖片分析
# ==========================================
def analyze_food_image(api_key, image_path, mime_type):
    genai.configure(api_key=api_key)
    prompt = """
    角色: 香菇爸 (專業寵物營養師與評測員)。
    任務: 分析寵物食品成分表。
    輸出格式: JSON。
    欄位: product_name, score(1-10), top_5_ingredients(array), benefits(string), good_points(array), bad_points(array), nutrition_analysis(string), verdict(string), suitable_for(string).
    """
    with st.spinner('🍄 香菇爸正在檢查成分表...'):
        try:
            img_file = genai.upload_file(path=image_path, mime_type=mime_type)
        except Exception as e:
            st.error(f"上傳失敗: {e}")
            return None
        while img_file.state.name == "PROCESSING":
            time.sleep(0.5)
            img_file = genai.get_file(img_file.name)
        for model_name in CANDIDATE_MODELS:
            try:
                model = genai.GenerativeModel(model_name=model_name, generation_config={"response_mime_type": "application/json"})
                response = model.generate_content([img_file, prompt])
                result = json.loads(clean_json_response(response.text))
                if isinstance(result, list): result = result[0]
                return result
            except: continue
        st.error("無法辨識圖片，請確認照片清晰。")
        return None

# ==========================================
# 功能 C: 熱量與餵食計畫
# ==========================================
def generate_diet_plan(api_key, cat_profile, calories, water_need):
    genai.configure(api_key=api_key)
    
    prompt = f"""
    角色: 香菇爸 (專業貓咪營養師)。
    任務: 根據貓咪數據，提供餵食建議與乾濕食搭配。
    [貓咪數據] {cat_profile}
    每日建議熱量: {calories:.0f} kcal, 水分: {water_need:.0f} ml.
    輸出格式: JSON。
    欄位: feeding_guide, water_tips, breed_advice, snack_limit, encouragement.
    """

    with st.spinner('🍄 香菇爸正在計算最佳菜單...'):
        for model_name in CANDIDATE_MODELS:
            try:
                model = genai.GenerativeModel(model_name=model_name, generation_config={"response_mime_type": "application/json"})
                response = model.generate_content(prompt)
                result = json.loads(clean_json_response(response.text))
                if isinstance(result, list): result = result[0]
                return result
            except: continue
        st.error("AI 忙碌中。")
        return None

# ==========================================
# 主畫面邏輯
# ==========================================

if app_mode == "🐱 貓咪讀心術 (影片)":
    st.title("🐱 香菇爸的貓咪讀心術")
    st.markdown("### 📸 上傳影片，解鎖主子在想什麼！")
    uploaded_file = st.file_uploader("上傳影片", type=["mp4", "mov", "avi", "webm", "mkv"])
    
    if uploaded_file:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: st.video(uploaded_file)
        if st.button("🔍 開始分析", type="primary", use_container_width=True):
            if not api_key: st.warning("請輸入 Key")
            else:
                file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                mime_types = {".mov": "video/quicktime", ".mp4": "video/mp4", ".avi": "video/x-msvideo", ".webm": "video/webm"}
                fix_mime = mime_types.get(file_ext, "video/mp4")
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
                tfile.write(uploaded_file.read())
                tfile.close()
                try:
                    result = analyze_video(api_key, tfile.name, fix_mime)
                    if result:
                        st.divider()
                        st.header("🗣️ 貓皇聖旨")
                        st.success(f"### 「{result.get('translation', '...')}」")
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.subheader("🎭 情緒")
                            st.info(result.get('mood'))
                        with c2:
                            st.subheader("💞 親密指數")
                            st.progress(result.get('intimacy_score', 0)/100)
                            st.caption(f"{result.get('intimacy_score')}/100")
                        with c3:
                            st.subheader("🍔 身材評鑑")
                            st.write("🍖" * result.get('chonk_score', 5))
                            st.caption(result.get('chonk_comment'))
                        st.divider()
                        st.markdown(f"#### 🏷️ MBTI: {result.get('cat_mbti')} | 標籤: `{result.get('hashtags')}`")
                        st.divider()
                        st.markdown("### 😲 覺得準嗎？")
                        cc1, cc2 = st.columns(2)
                        with cc1: st.link_button("📺 看更多香菇爸影片", YOUR_CHANNEL_LINK, use_container_width=True)
                        with cc2: st.link_button("🎁 領取養貓懶人包", YOUR_LINE_LINK, type="primary", use_container_width=True)
                except Exception as e: st.error(f"錯誤: {e}")
                finally: 
                    if os.path.exists(tfile.name): os.remove(tfile.name)

elif app_mode == "🥫 飼料罐頭分析 (照片)":
    st.title("🥫 香菇爸的食安官")
    st.markdown("### 📸 拍下 **「成分表」**，AI 幫你把關！")
    uploaded_img = st.file_uploader("上傳照片", type=["jpg", "png", "jpeg", "webp"])
    
    if uploaded_img:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: st.image(uploaded_img)
        if st.button("🔍 開始分析成分", type="primary", use_container_width=True):
            if not api_key: st.warning("請輸入 Key")
            else:
                file_ext = os.path.splitext(uploaded_img.name)[1].lower()
                mime = "image/jpeg" if file_ext in [".jpg", ".jpeg"] else "image/png"
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
                tfile.write(uploaded_img.read())
                tfile.close()
                try:
                    result = analyze_food_image(api_key, tfile.name, mime)
                    if result:
                        st.divider()
                        st.header(f"📦 {result.get('product_name', '產品')}")
                        c1, c2 = st.columns(2)
                        with c1:
                            score = result.get('score', 5)
                            color = "green" if score >= 8 else "orange" if score >= 5 else "red"
                            st.markdown(f":{color}[## 🏆 {score} / 10 分]")
                        with c2:
                            st.info(f"🐱 適合：{result.get('suitable_for')}")
                        st.divider()
                        st.subheader("🥩 前五大成分")
                        top5 = result.get('top_5_ingredients', [])
                        st.write("、".join(top5))
                        st.success(f"💪 **好處：** {result.get('benefits')}")
                        st.divider()
                        c3, c4 = st.columns(2)
                        with c3:
                            st.subheader("✅ 優點")
                            for p in result.get('good_points', []): st.success(p)
                        with c4:
                            st.subheader("⚠️ 注意")
                            for p in result.get('bad_points', []): st.error(p)
                        st.divider()
                        st.info(f"🍄 **香菇爸點評：** {result.get('verdict')}")
                        st.warning("⚠️ 免責聲明：若貓咪有特殊疾病，請務必諮詢獸醫。")
                        st.divider()
                        cc1, cc2 = st.columns(2)
                        with cc1: st.link_button("📺 看更多香菇爸影片", YOUR_CHANNEL_LINK, use_container_width=True)
                        with cc2: st.link_button("🎁 領取食安懶人包", YOUR_LINE_LINK, type="primary", use_container_width=True)
                except Exception as e: st.error(f"錯誤: {e}")
                finally:
                    if os.path.exists(tfile.name): os.remove(tfile.name)

elif app_mode == "📊 熱量&喝水計算機":
    st.title("📊 貓咪熱量 & 喝水計算機")
    st.markdown("### 📝 輸入資料，算出主子 **每天該吃多少、喝多少**！")
    
    with st.form("cat_form"):
        c1, c2 = st.columns(2)
        with c1:
            # 🌟 21種品種清單 + 其他
            breed_options = [
                "米克斯 (Mix)", 
                "英國短毛貓 (British Shorthair)", 
                "美國短毛貓 (American Shorthair)", 
                "布偶貓 (Ragdoll)", 
                "波斯貓 (Persian)", 
                "曼赤肯 (Munchkin)", 
                "蘇格蘭摺耳貓 (Scottish Fold)", 
                "暹羅貓 (Siamese)", 
                "斯芬克斯無毛貓 (Sphynx)", 
                "緬因貓 (Maine Coon)", 
                "俄羅斯藍貓 (Russian Blue)", 
                "孟加拉貓/豹貓 (Bengal)", 
                "異國短毛貓/加菲貓 (Exotic)", 
                "挪威森林貓 (Norwegian Forest)", 
                "阿比西尼亞貓 (Abyssinian)", 
                "德文捲毛貓 (Devon Rex)", 
                "東方短毛貓 (Oriental Shorthair)", 
                "伯曼貓 (Birman)", 
                "西伯利亞貓 (Siberian)", 
                "緬甸貓 (Burmese)", 
                "埃及貓 (Egyptian Mau)", 
                "其他 (自行輸入)"
            ]
            selected_breed = st.selectbox("🐈 貓咪品種", breed_options)
            
            if selected_breed == "其他 (自行輸入)":
                cat_breed = st.text_input("請輸入品種名稱", "米克斯")
            else:
                cat_breed = selected_breed

            # 滑桿設定
            cat_age = st.slider("🎂 年齡 (歲)", 0.1, 25.0, 3.0, 0.1)
            cat_gender = st.radio("⚧️ 性別", ["公", "母"], horizontal=True)
            
        with c2:
            cat_weight = st.slider("⚖️ 體重 (kg)", 0.1, 20.0, 4.0, 0.1)
            cat_status = st.selectbox("🩺 身體狀態 (決定熱量係數)", 
                ["已結紮 (標準)", "未結紮 (活動力高)", "過胖/減肥中", "幼貓 (生長中)", "高齡貓 (活動力低)"])
            cat_preference = st.selectbox("🍲 飲食偏好", ["以乾飼料為主", "以濕食(罐頭/生食)為主", "半濕半乾 (一半一半)"])
            
        submitted = st.form_submit_button("🍄 香菇爸幫我算！", type="primary", use_container_width=True)

    if submitted:
        if not api_key:
            st.warning("請先在左側輸入 API Key")
        else:
            rer = 70 * (cat_weight ** 0.75)
            factor = 1.2
            if "未結紮" in cat_status: factor = 1.4
            elif "過胖" in cat_status: factor = 0.8
            elif "幼貓" in cat_status: factor = 2.0
            elif "高齡" in cat_status: factor = 1.0
            
            daily_calories = rer * factor
            daily_water = cat_weight * 50
            
            cat_profile = {
                "breed": cat_breed, "age": cat_age, "weight": cat_weight,
                "status": cat_status, "preference": cat_preference
            }
            
            plan = generate_diet_plan(api_key, cat_profile, daily_calories, daily_water)
            
            if plan:
                st.divider()
                m1, m2, m3 = st.columns(3)
                m1.metric("🔥 每日熱量 (kcal)", f"{daily_calories:.0f}")
                m2.metric("💧 每日喝水 (ml)", f"{daily_water:.0f}")
                m3.metric("⚖️ 體重 (kg)", f"{cat_weight}")
                
                st.divider()
                st.subheader("🍽️ 香菇爸的餵食建議")
                st.info(f"💡 {plan.get('feeding_guide')}")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("💧 騙水小技巧")
                    st.success(plan.get('water_tips'))
                with c2:
                    st.subheader("🧬 品種/年齡特別注意")
                    st.warning(plan.get('breed_advice'))
                
                st.divider()
                st.write(f"🍪 **零食上限：** {plan.get('snack_limit')}")
                st.markdown(f"#### 🍄 **給家長的話：**\n{plan.get('encouragement')}")
                
                st.divider()
                cc1, cc2 = st.columns(2)
                with cc1: st.link_button("📺 看更多香菇爸影片", YOUR_CHANNEL_LINK, use_container_width=True)
                with cc2: st.link_button("🎁 領取營養計算懶人包", YOUR_LINE_LINK, type="primary", use_container_width=True)
