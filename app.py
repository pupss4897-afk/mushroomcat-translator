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
st.set_page_config(page_title="香菇爸的貓咪讀心術 & 食安官", page_icon="🍄", layout="wide")

# ==========================================
# 2. 側邊欄：個人品牌與導流
# ==========================================
st.sidebar.title("🍄 關於香菇爸")
st.sidebar.info("嗨！我是香菇爸，專精於貓科動物行為與營養分析。")

YOUR_CHANNEL_LINK = "https://www.instagram.com/love_mushroom55?igsh=NTl4bmg2djJyejFn&utm_source=qr" 
YOUR_LINE_LINK = "https://s.luckycat.no8.io/link/channels/ZIGreweSIw"

st.sidebar.markdown("### 📢 追蹤更多")
st.sidebar.link_button("📺 前往香菇爸的頻道", YOUR_CHANNEL_LINK, use_container_width=True)
st.sidebar.link_button("🎁 加 LINE 領取「貓咪懶人包」", YOUR_LINE_LINK, type="primary", use_container_width=True)

st.sidebar.markdown("---")

# 功能切換選單
app_mode = st.sidebar.radio(
    "請選擇功能：",
    ["🐱 貓咪讀心術 (影片)", "🥫 飼料罐頭分析 (照片)"]
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

# 候選模型名單
CANDIDATE_MODELS = [
    "gemini-1.5-flash",          
    "gemini-1.5-flash-001",
    "gemini-1.5-pro",            
    "gemini-2.0-flash",
    "gemini-flash-latest"
]

# ==========================================
# 功能 A: 影片分析 (讀心術)
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
            except:
                continue
        
        st.error("抱歉，AI 線路忙碌中，請稍後再試。")
        return None

# ==========================================
# 功能 B: 圖片分析 (升級版食安官)
# ==========================================
def analyze_food_image(api_key, image_path, mime_type):
    genai.configure(api_key=api_key)
    
    # 🌟 升級 Prompt：加入前五成分、優勢、扣分原因
    prompt = """
    角色: 香菇爸 (專業寵物營養師與評測員)。
    任務: 分析這張寵物食品(飼料/罐頭)的成分表或營養標示圖片。
    輸出格式: JSON (請確保由 JSON 解析)。
    
    請分析以下欄位：
    1. product_name (字串): 產品名稱 (若無則寫"未知產品")。
    2. score (整數 1-10): 綜合營養評分。
    3. top_5_ingredients (字串陣列): 列出排名前五的主要成分 (這是判斷關鍵)。
    4. benefits (字串): 這些主要成分對貓咪有什麼好處？(例如: 雞肉提供優質蛋白長肌肉、魚油護膚)。
    5. good_points (字串陣列): 其他優點 (例如: 無穀、低碳水)。
    6. bad_points (字串陣列): 扣分項目與原因 (格式: "成分名稱 - 為什麼不好")。例如: "卡拉膠 - 可能引起腸胃發炎"。
    7. nutrition_analysis (字串): 針對蛋白質/脂肪/碳水的簡短評價。
    8. verdict (字串): 香菇爸的總結購買建議。
    9. suitable_for (字串): 適合對象 (例如: 腎貓慎用、全齡貓)。
    """

    with st.spinner('🍄 香菇爸正在拿放大鏡檢查成分表...'):
        try:
            img_file = genai.upload_file(path=image_path, mime_type=mime_type)
        except Exception as e:
            st.error(f"圖片上傳失敗: {e}")
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
            except:
                continue
        
        st.error("無法辨識圖片，請確認照片清晰包含成分表。")
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
        
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if st.button("🔍 開始分析", type="primary", use_container_width=True):
            if not api_key:
                st.warning("⚠️ 請輸入 API Key")
            else:
                mime_types = {".mov": "video/quicktime", ".mp4": "video/mp4", ".avi": "video/x-msvideo", ".webm": "video/webm"}
                fix_mime = mime_types.get(file_extension, "video/mp4")
                
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
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
                            st.write(f"🧐 {result.get('reasoning')}")
                        with c2:
                            st.subheader("💞 親密指數")
                            st.progress(result.get('intimacy_score', 0)/100)
                            st.write(f"**{result.get('intimacy_score', 0)} / 100**")
                        with c3:
                            st.subheader("🍔 身材評鑑")
                            chonk = result.get('chonk_score', 5)
                            st.write("🍖" * chonk + "░" * (10 - chonk))
                            st.write(f"*{result.get('chonk_comment')}*")
                        
                        st.divider()
                        st.markdown(f"#### 🏷️ MBTI: {result.get('cat_mbti')} | 標籤: `{result.get('hashtags')}`")
                        
                        st.divider()
                        st.markdown("### 😲 覺得準嗎？")
                        cc1, cc2 = st.columns(2)
                        with cc1: st.link_button("📺 看更多香菇爸影片", YOUR_CHANNEL_LINK, use_container_width=True)
                        with cc2: st.link_button("🎁 領取養貓懶人包", YOUR_LINE_LINK, type="primary", use_container_width=True)

                except Exception as e:
                    st.error(f"出錯了: {e}")
                finally:
                    if os.path.exists(tfile.name): os.remove(tfile.name)

elif app_mode == "🥫 飼料罐頭分析 (照片)":
    st.title("🥫 香菇爸的食安官")
    st.markdown("### 📸 拍下 **「成分表」** 或 **「營養標示」**，AI 幫你把關！")
    
    uploaded_img = st.file_uploader("上傳成分表照片", type=["jpg", "png", "jpeg", "webp"])
    
    if uploaded_img:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: st.image(uploaded_img, caption="預覽圖片")
        
        if st.button("🔍 開始分析成分", type="primary", use_container_width=True):
            if not api_key:
                st.warning("⚠️ 請輸入 API Key")
            else:
                file_extension = os.path.splitext(uploaded_img.name)[1].lower()
                mime_type = "image/jpeg" if file_extension in [".jpg", ".jpeg"] else "image/png"
                
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
                tfile.write(uploaded_img.read())
                tfile.close()
                
                try:
                    result = analyze_food_image(api_key, tfile.name, mime_type)
                    if result:
                        st.divider()
                        st.header(f"📦 產品：{result.get('product_name', '未知產品')}")
                        
                        # 第一排：分數與適合對象
                        c1, c2 = st.columns(2)
                        with c1:
                            st.subheader("🏆 營養評分")
                            score = result.get('score', 5)
                            color = "green" if score >= 8 else "orange" if score >= 5 else "red"
                            st.markdown(f":{color}[## {score} / 10 分]")
                        with c2:
                            st.subheader("🐱 適合對象")
                            st.info(f"{result.get('suitable_for')}")
                        
                        st.divider()
                        
                        # 🌟 新增區塊：前五大成分 & 好處
                        st.subheader("🥩 前五大成分 (Key Ingredients)")
                        top_5 = result.get('top_5_ingredients', [])
                        if top_5:
                            # 用標籤顯示成分
                            st.write("、".join([f"**{item}**" for item in top_5]))
                            # 顯示好處
                            st.success(f"💪 **吃這些有什麼好處？**\n\n{result.get('benefits', '提供基礎營養')}")
                        
                        st.divider()

                        # 第三排：優缺點 PK (顯示扣分原因)
                        c3, c4 = st.columns(2)
                        with c3:
                            st.subheader("✅ 優點")
                            for point in result.get('good_points', []):
                                st.success(f"📍 {point}")
                        with c4:
                            st.subheader("⚠️ 注意/扣分")
                            bad_points = result.get('bad_points', [])
                            if not bad_points:
                                st.write("無明顯重大缺失")
                            else:
                                for point in bad_points:
                                    # 這裡會顯示 "成分 - 原因"
                                    st.error(f"📍 {point}")
                        
                        st.divider()
                        st.subheader("🔬 營養分析")
                        st.write(result.get('nutrition_analysis'))
                        
                        st.divider()
                        st.subheader("🍄 香菇爸點評")
                        st.info(f"「{result.get('verdict')}」")
                        
                        # 🌟 醫療免責聲明 (一定要加！)
                        st.warning("⚠️ **免責聲明**：本分析由 AI 根據成分表生成，僅供參考。若您的貓咪有特殊疾病（如腎臟病、糖尿病），請務必諮詢專業獸醫師，以醫囑為準。")

                        st.divider()
                        st.markdown("### 😲 想學更多寵物營養？")
                        cc1, cc2 = st.columns(2)
                        with cc1: st.link_button("📺 看更多香菇爸影片", YOUR_CHANNEL_LINK, use_container_width=True)
                        with cc2: st.link_button("🎁 領取食安懶人包", YOUR_LINE_LINK, type="primary", use_container_width=True)

                except Exception as e:
                    st.error(f"出錯了: {e}")
                finally:
                    if os.path.exists(tfile.name): os.remove(tfile.name)
