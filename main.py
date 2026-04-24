import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pinecone import Pinecone
from datetime import datetime
import os, base64, asyncio, edge_tts
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 1. SETUP & CONNECTIONS ---
st.set_page_config(page_title="Rin v40.22 90B Vision Upgrade", layout="centered")

LINE_ACCESS_TOKEN = st.secrets.get("LINE_ACCESS_TOKEN")
MY_LINE_USER_ID = st.secrets.get("MY_LINE_USER_ID")
PINECONE_KEY = st.secrets.get("PINECONE_API_KEY")
TAVILY_KEY = st.secrets.get("TAVILY_API_KEY")

def send_line(text):
    if LINE_ACCESS_TOKEN and MY_LINE_USER_ID:
        try:
            line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
            line_bot_api.push_message(MY_LINE_USER_ID, TextSendMessage(text=text))
            return True
        except: return False
    return False

def get_memory(u_input):
    try:
        pc = Pinecone(api_key=PINECONE_KEY)
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=u_input)
        search = index.query(vector=res.data[0].embedding, top_k=2, include_metadata=True)
        return "\n".join([f"อดีตบอสเคยบอก: {m['metadata']['text']}" for m in search['matches']])
    except: return ""

def save_memory(u_input, r_output):
    try:
        pc = Pinecone(api_key=PINECONE_KEY)
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=u_input)
        index.upsert(vectors=[{"id": datetime.now().strftime("%Y%m%d%H%M%S"), "values": res.data[0].embedding, "metadata": {"text": u_input, "reply": r_output}}])
    except: pass

# --- 2. UI STYLE ---
RIN_AVATAR = "rin_avatar.jpg"
def get_avatar():
    return RIN_AVATAR if os.path.exists(RIN_AVATAR) else "👓"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff !important; }}
    * {{ color: #000000 !important; font-size: 19px; }}
    .stChatMessage {{ background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }}
    [data-testid="stChatMessageElement"] img {{ width: 65px !important; height: 65px !important; border-radius: 12px !important; border: 2px solid #DDA0DD !important; object-fit: cover; }}
    [data-testid="stChatMessageContent"] {{ margin-left: 15px !important; }}
    .action-container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }}
    .action-chip {{ display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; font-size: 16px !important; font-weight: bold; transition: 0.3s; text-align: center; }}
    .action-chip:hover {{ background-color: #DDA0DD; color: #ffffff !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
    div[data-testid="stRadio"] > div {{ flex-direction: row; align-items: center; justify-content: center; background-color: #f8f9fa; padding: 10px; border-radius: 15px; border: 1px solid #eee; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR): st.image(RIN_AVATAR, use_container_width=True)
    st.markdown("### 🏛️ Diana System Core")
    
    # 🟢 เพิ่มปุ่มเลือกโมเดลตา ให้บอสเทสได้ตามใจชอบเลยค่ะ!
    st.markdown("**👁️ ระบบตา (ดูรูปภาพ):**")
    vision_model = st.radio("เลือกตา:", ["llama-3.2-90b-vision-preview", "meta-llama/llama-4-scout-17b-16e-instruct"], label_visibility="collapsed")
    st.write("---")
    
    if st.button("🔍 ตรวจสอบสมองที่ใช้ได้"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            for m in client.models.list().data: st.code(m.id)
        except Exception as e: st.error(f"Error: {e}")

    search_mode = st.toggle("🔍 สแกนเน็ต", value=False)
    line_on = st.toggle("🟢 ส่งแจ้งเตือน LINE", value=True)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอ"): st.session_state.messages = []; st.rerun()

# --- 4. MAIN UI ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v40.22 90B Vision Upgrade</h2>", unsafe_allow_html=True)

st.markdown("""
    <div class="action-container">
        <a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 Maps</a>
        <a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>
        <a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>
        <a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>
    </div>
    """, unsafe_allow_html=True)

mode = st.radio("🧠 ระบบสมอง (คุยข้อความ):", ["⚡ Fast (8B)", "🧠 Ultra (70B)"], horizontal=True)
text_model_id = "llama-3.1-8b-instant" if "Fast" in mode else "llama-3.3-70b-versatile"

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=get_avatar() if m["role"]=="assistant" else None):
        if "image" in m: st.image(m["image"], width=300)
        st.markdown(m["content"])

# --- 5.
