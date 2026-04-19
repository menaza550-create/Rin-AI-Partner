import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64, asyncio, edge_tts, pandas as pd

# --- 1. การตั้งค่าหน้าตาแอป ---
st.set_page_config(
    page_title="Rin-ai v34.9 Partner", 
    layout="centered",
    initial_sidebar_state="expanded" 
)

# ฝัง API Key ที่บอสให้มา (Gemini Key)
GEMINI_API_KEY = "AIzaSyDFrM43Dh-wYNbda5UvmLbPmpySiPYXtsw"

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 18px !important; }
    .stButton>button { border-radius: 20px; font-weight: bold; width: 100%; height: 50px; }
    .crypto-card { background-color: #f8f9fa; padding: 15px; border-radius: 12px; border-left: 6px solid #DDA0DD; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ระบบจัดการ Google Sheets ---
def get_gsheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open("Rin_Memory").worksheet("customer_data")
    except: return None

def read_last_memory(limit=10):
    sheet = get_gsheet()
    if not sheet: return "ระบบความจำขัดข้องค่ะ"
    try:
        data = sheet.get_all_values()
        return "\n".join([f"- {r[0]}: {r[2]}" for r in data[-limit:]])
    except: return "รินรื้อสมุดจดไม่สำเร็จค่ะ"

# --- 3. ฟังก์ชันร่างริน & เสียง ---
async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

# --- 4. Sidebar: แผงควบคุม ---
with st.sidebar:
    st.markdown("## 📂 Project: Rin-ai")
    st.info("สถานะ: บังคับเปิดเมนูตลอดเวลา 👓")
    
    # ดึงราคา LUNC อัตโนมัติ (ถ้ามี Tavily Key ใน Secrets)
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        p_res = tavily.search(query="LUNC price USD", max_results=1)
        st.markdown(f'<div class="crypto-card"><b>LUNC Status:</b><br>{p_res["results"][0]["content"][:60]}...</div>', unsafe_allow_html=True)
    except: st.write("📊 ระบบ Dashboard พร้อมรับคำสั่งค่ะ")

    voice_on = st.toggle("เปิดเสียงริน", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

# --- 5. หน้าจอหลัก ---
st.markdown("<h2 style='text-align:center;'>Rin-ai Partner v34.9</h2>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 6. ACTION CHIPS (Phase 3: ทางลัดเปิดแอปตามสั่ง) ---
st.write("---")
st.markdown("### 🚀 ทางลัดด่วน")
c1, c2, c3, c4 = st.columns(4)
action_prompt = None

# ปุ่ม 1: นำทาง (Google Maps)
if c1.button("📍 นำทาง"):
    st.markdown('<a href="https://www.google.com/maps/dir/?api=1&destination=Pattaya" target="_blank">🚩 กดเพื่อไป Maps</a>', unsafe_allow_html=True)
    action_prompt = "แนะนำที่เที่ยวพัทยาเจ๋งๆ ให้บอสหน่อยค่ะ"

# ปุ่ม 2: YouTube
if c2.button("📺 YouTube"):
    st.markdown('<a href="https://www.youtube.com" target="_blank">🎬 เข้า YouTube</a>', unsafe_allow_html=True)

# ปุ่ม 3: Facebook
if c3.button("👥 Facebook"):
    st.markdown('<a href="https://www.facebook.com" target="_blank">🌐 เข้า Facebook</a>', unsafe_allow_html=True)

# ปุ่ม 4: Line
if c4.button("💬 Line"):
    st.markdown('<a href="https://line.me/R/" target="_blank">🟢 เปิด Line</a>', unsafe_allow_html=True)

# --- 7. ส่วนรับคำสั่ง ---
col_mic, col_in = st.columns([1, 5])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#DDA0DD")

prompt = st.chat_input("สั่งงานรินได้เลยค่ะบอส...")
final_input = action_prompt if action_prompt else prompt

if audio:
    with st.spinner("รินกำลังฟัง..."):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "wb") as f: f.write(audio)
        with open("t.wav", "rb") as f:
            final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        past_memory = read_last_memory(5)
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # คุยกับริน (Llama 3.3)
        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": f"คุณคือริน AI เลขาส่วนตัวของบอสคิริลิ (Piyawut) ที่พัทยา ความจำล่าสุด: {past_memory}. ตอบหวานๆ และฉลาดค่ะ"},
                      *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]]
        )
        answer = chat.choices[0].message.content
        
        st.markdown(answer)
        if voice_on:
            asyncio.run(make_voice(answer))
            st.audio("rin_voice.mp3", autoplay=True)
        st.session_state.messages.append({"role": "assistant", "content": answer})
