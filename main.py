import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pyairtable import Api
from datetime import datetime
import os, base64, asyncio, edge_tts
from PIL import Image
import io

# --- 1. การตั้งค่าหน้าตาแอป (UI & Styling) ---
st.set_page_config(page_title="Rin v34.8 Partner", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 19px; }
    .stChatMessage { background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }
    .crypto-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #DDA0DD; margin-bottom: 15px;}
    .action-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }
    .action-chip { display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; font-size: 16px !important; font-weight: bold; transition: 0.3s; text-align: center; }
    .action-chip:hover { background-color: #DDA0DD; color: #ffffff !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันระบบจัดการ (ML & Audio & Memory) ---
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def play_audio_hidden(file_path):
    """เล่นเสียงแบบซ่อนแถบเครื่องเล่น เพื่อความมืออาชีพ 👓"""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)

async def make_voice(text):
    # ปรับโทนเสียงให้สุขุมขึ้นแบบ Diana Mode
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-10%", pitch="+2Hz")
    await communicate.save("rin_voice.mp3")

@st.cache_data(ttl=300)
def fetch_lunc_price():
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        res = tavily.search(query="LUNC price USD today", max_results=1)
        return res["results"][0]["content"][:120]
    except: return "ดึงข้อมูลราคาไม่ได้ค่ะ"

def get_airtable_table():
    try:
        api = Api(st.secrets["AIRTABLE_TOKEN"])
        return api.table(st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])
    except: return None

@st.cache_data(ttl=60)
def read_last_memory(limit=3):
    try:
        table = get_airtable_table()
        if not table: return ""
        records = table.all(max_records=limit, sort=["-Date"])
        return "\n".join([f"- อดีต: {r['fields'].get('User')}" for r in records])
    except: return ""

# --- 3. Sidebar & Status Dashboard ---
with st.sidebar:
    st.markdown("### 📊 Business & ML Status")
    lunc_info = fetch_lunc_price()
    st.markdown(f'<div class="crypto-card"><b>LUNC Status:</b><br>{lunc_info}...</div>', unsafe_allow_html=True)
    st.info("Brain: Llama 3.3 70B\nVision: Llama 3.2 90B\nStatus: Online 🟢")
    st.divider()
    search_mode = st.toggle("🔍 โหมดหาข้อมูล (Web Search)", value=False)
    voice_on = st.toggle("🔊 เปิดเสียงเลขา", value=True)
    if st.button("🗑️ ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

# --- 4. Main UI ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v34.8 Partner</h2>", unsafe_allow_html=True)
st.markdown('<div class="action-container">'
    '<a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a>'
    '<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>'
    '<a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>'
    '<a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>'
    '</div>', unsafe_allow_html=True)
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. Perception Layer (Input) ---
with st.container():
    uploaded_file = st.file_uploader("ส่งรูปภาพให้รินวิเคราะห์ (บิล/กราฟ/โฆษณา)", type=["jpg", "jpeg", "png"])
    col_mic, col_input = st.columns([1, 6])
    with col_mic: audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
    prompt = st.chat_input("สั่งการรินได้เลยค่ะบอส...")

final_input = None
if audio:
    with st.spinner("กำลังฟัง..."):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            with open("temp.wav", "wb") as f: f.write(audio)
            with open("temp.wav", "rb") as f:
                ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
                final_input = ts.text
        except: st.error("ไมค์ขัดข้อง")
elif prompt: final_input = prompt

# --- 6. Brain Layer (Processing) ---
if final_input or uploaded_file:
    user_
