import streamlit as st
import google.generativeai as genai
import sys

st.title("🔧 系統診斷模式")

# 1. 檢查 Python 和工具包版本
st.subheader("1. 環境檢查")
st.write(f"Python Version: `{sys.version}`")
try:
    st.write(f"Google GenAI SDK Version: `{genai.__version__}`")
    if genai.__version__ < "0.8.3":
        st.error("❌ 版本過舊！需要 0.8.3 以上")
    else:
        st.success(f"✅ 版本正常 ({genai.__version__})")
except Exception as e:
    st.error(f"❌ 無法讀取 SDK 版本: {e}")

# 2. 檢查 API Key
st.subheader("2. 金鑰檢查")
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    # 遮蔽中間，只顯示頭尾，確認有沒有讀錯
    masked_key = api_key[:5] + "..." + api_key[-3:]
    st.success(f"✅ 成功讀取 Secrets (Key: {masked_key})")
    genai.configure(api_key=api_key)
else:
    st.error("❌ 找不到 Secrets 裡的 GOOGLE_API_KEY，請去 Streamlit 後台設定！")

# 3. 實測模型連線 (最重要的一步)
st.subheader("3. 雲端模型連線測試")
if st.button("開始掃描可用模型"):
    try:
        st.info("正在詢問 Google 伺服器...")
        models = genai.list_models()
        
        found_any = False
        st.write("--- Google 回傳的模型清單 ---")
        
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                st.write(f"✅ `{m.name}`")
                found_any = True
        
        if not found_any:
            st.error("😱 Google 連線成功，但回傳的清單是空的！(可能是 API Key 權限問題)")
        else:
            st.balloons()
            st.success("測試成功！請看上面有哪些名字，我們就用那個！")
            
    except Exception as e:
        st.error("❌ 連線發生錯誤 (詳細原因如下)")
        st.code(e)
