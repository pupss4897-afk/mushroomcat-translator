import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
import json
import re
import traceback

# ==========================================
# 1. 網頁設定
# ==========================================
st.set_page_config(page_title="香菇爸的貓咪讀心術", page_icon="🍄", layout="wide")

# ==========================================
# 2. 側邊欄
# ==========================================
st.sidebar.title("🍄 關於香菇爸")
st.sidebar.info("嗨！我是香菇爸，專精於貓科動物行為分析。這是一個用 AI 幫你聽懂主子心聲的小工具！")

YOUR_CHANNEL_LINK = "https://www.instagram.com/love_mushroom55?igsh=NTl4bmg2djJyejFn&utm_source=qr" 
YOUR_LINE_LINK = "https://s.luckycat.no8.io/link/channels/ZIGreweSIw"

st.sidebar.markdown("### 📢 追蹤更多")
st.sidebar.link_button("📺 前往香菇爸的頻道看影片", YOUR_CHANNEL_LINK, use_container_width=True)
st.sidebar.link_button("🎁 加 LINE 領取「貓咪懶人包」", YOUR_LINE_LINK, type="primary", use_container_width=True)

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

# ==========================================
# 核心功能函數 (回歸最穩定的 1.5 Flash)
# ==========================================
def analyze_video(api_key, video_path, mime_type):
    genai.configure(api_key=api_key)
    
    # 🌟 使用最標準、額度最高的 1.5 Flash
    # 因為我們更新了 requirements.txt，這次一定找得到它！
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        generation_config={"response_mime_type": "application/json"}
    )
    
    prompt = """
    角色: 香菇爸 (資深動物行為學家與貓咪溝通師)。
    任務: 分析貓咪影片的視覺與聽覺，解讀情緒與特徵。
    輸出格式: JSON。
    
    請分析以下欄位：
    1. mood (字串): 當下情緒 (如: 慵懶、狩獵中、鄙視人類)。
    2. intimacy_score (整數 0-100): 親密度。
    3. translation (字串): 第一人稱貓語翻譯 (風格生動、用詞要像貓)。
    4. reasoning (字串): 判斷依據 (看到什麼動作/聽到什麼聲音)。
    5. suggestion (字串): 給奴才的建議 (以香菇爸的口吻建議)。
    6. chonk_score (整數 1-10): 身材圓潤度 (1是極瘦，10是超級胖/阿嬤養的)。
    7. chonk_comment (字串): 對身材的幽默評語。
    8. cat_mbti (字串): 貓咪的性格類型 (例如: 霸道總裁型、傻白甜型)。
    9. hashtags (字串): 適合發在 Instagram 的 5 個標籤。
    """

    with st.spinner('🍄 香菇爸正在跟 AI 連線幫你看貓貓...'):
        try:
            video_file = genai.upload_file(path=video_path, mime_type=mime_type)
        except Exception as e:
            st.error(f"上傳檔案時發生錯誤: {e}")
            return None
        
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)
            
        if video_file.state.name == "FAILED":
            st.error("❌ 影片處理失敗。可能原因：影片格式不支援。")
            return None

        try:
            response = model.generate_content([video_file, prompt])
            
            try:
                genai.delete_file(video_file.name)
            except:
                pass
            
            clean_text = clean_json_response(response.text)
            json_data = json.loads(clean_text)
            if isinstance(json_data, list): return json_data[0]
            return json_data
            
        except Exception as e:
            st.error(f"AI 分析時發生錯誤: {e}")
            return None

# ==========================================
# 主畫面
# ==========================================
st.title("🍄 香菇爸的貓咪讀心術")
st.markdown("### 📸 上傳影片，讓香菇爸幫你解鎖 **主子在想什麼**！")

uploaded_file = st.file_uploader("", type=["mp4", "mov", "avi", "webm", "mkv"])

if uploaded_file is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.video(uploaded_file)
    
    # 變數定義在這邊，保證安全
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        analyze_btn = st.button("🔍 香菇爸幫我看！", type="primary", use_container_width=True)

    if analyze_btn:
        if not api_key:
            st.warning("⚠️ 請輸入 API Key 才能使用喔！")
        else:
            mime_types = {
                ".mov": "video/quicktime", ".mp4": "video/mp4", ".avi": "video/x-msvideo",
                ".webm": "video/webm", ".mkv": "video/x-matroska", ".3gp": "video/3gpp"
            }
            fix_mime_type = mime_types.get(file_extension, "video/mp4")

            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) 
            tfile.write(uploaded_file.read())
            tfile.close()
            
            try:
                result = analyze_video(api_key, tfile.name, fix_mime_type)
                
                if result:
                    st.divider()
                    st.header("🗣️ 貓皇聖旨")
                    st.success(f"### 「{result.get('translation', '人類，朕不想說話')}」")
                    st.divider()

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.subheader("🎭 當下情緒")
                        st.info(f"**{result.get('mood', '未知')}**")
                        st.write(f"🧐 **判斷:** {result.get('reasoning')}")
                    with c2:
                        st.subheader("💞 親密指數")
                        score = result.get('intimacy_score', 0)
                        st.progress(score / 100)
                        st.write(f"**{score} / 100 分**")
                        st.caption(result.get('suggestion'))
                    with c3:
                        st.subheader("🍔 身材評鑑")
                        chonk = result.get('chonk_score', 5)
                        chonk_bar = "🍖" * chonk + "░" * (10 - chonk)
                        st.write(f"{chonk_bar}")
                        st.write(f"**等級: {chonk}/10**")
                        st.write(f"📝 *{result.get('chonk_comment')}*")

                    st.divider()
                    c4, c5 = st.columns(2)
                    with c4:
                        st.subheader("🧠 貓格 MBTI")
                        st.markdown(f"#### 🏷️ {result.get('cat_mbti', '謎樣的貓')}")
                    with c5:
                        st.subheader("✨ 網紅標籤")
                        tags = result.get('hashtags', '#香菇爸 #貓')
                        st.code(tags, language="markdown")
                    
                    st.divider()
                    st.markdown("### 😲 覺得準嗎？想了解更多貓咪知識？")
                    cta_col1, cta_col2 = st.columns(2)
                    with cta_col1:
                        st.link_button("📺 點我看更多香菇爸的影片", YOUR_CHANNEL_LINK, use_container_width=True)
                    with cta_col2:
                        st.link_button("🎁 加 LINE 免費領「養貓懶人包」", YOUR_LINE_LINK, type="primary", use_container_width=True)

            except Exception as e:
                st.error("系統出錯了！請截圖給工程師")
                st.code(traceback.format_exc())
            finally:
                if os.path.exists(tfile.name): os.remove(tfile.name)
