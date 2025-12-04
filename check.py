import google.generativeai as genai

# ==========================================
# 🛑 請去 cat.py 複製那個「已經修好」的 Key 貼過來
# ==========================================
API_KEY = "AIzaSyCYBLgoBazUFbSk2OvYBRYsUG_-4TyyEGY"

genai.configure(api_key=API_KEY.strip())

print(f"📊 目前使用的套件版本: {genai.__version__}")
print("🔍 正在查詢你的帳號可用模型清單...")
print("---------------------------------------")

try:
    found_any = False
    for m in genai.list_models():
        # 我們只找可以「生成內容」的模型
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ {m.name}")
            found_any = True
    
    if not found_any:
        print("😱 奇怪，清單是空的！")
        
except Exception as e:
    print(f"❌ 查詢失敗: {e}")

print("---------------------------------------")