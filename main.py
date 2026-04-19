import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64, asyncio, edge_tts, pandas as pd

# --- [SETTING] ตั้งค่าหน้าตาแอป ---
st.set_page_config(page_title="Rin v34.9 Utility Partner", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 18px !important; }
    .stChatMessage { border-radius: 12px; border: 1px solid #eee; margin-bottom: 10px; }
    .action-chip {
        display: inline-block; padding: 8px 16px; margin: 5px; border-radius: 20px;
        background-color: #f0f2f6; border: 1px solid #DDA0DD; text-decoration: none;
        color: #000 !important; font-size: 14px !important; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. ระบบความจำ & เสียง ---
def get_gsheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open("Rin_Memory").worksheet("customer_data")
    except: return None

async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("📂 Project: Rin-ai")
    st.info("✅ Phase 1: Deep Memory\n⏳ Phase 2: Mobile Control")
    st.divider()
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

# --- 3. หน้าจอหลัก & แสดงแชท ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v34.9 Partner</h2>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "autoplay_audio" not in st.session_state: st.session_state.autoplay_audio = False

# [FIX] ส่วนการแสดงแชทที่ทำให้รินพูดเองได้
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # ตรวจสอบว่าต้องเล่นเสียงอัตโนมัติสำหรับข้อความล่าสุดไหม
            if i == len(st.session_state.messages) - 1 and st.session_state.autoplay_audio:
                if os.path.exists("rin_voice.mp3") and voice_on:
                    st.audio("rin_voice.mp3", autoplay=True)
                    st.session_state.autoplay_audio = False # เล่นแล้วปิดทันที กันลูปซ้ำ

            u1, u2, _ = st.columns([0.1, 0.1, 0.8])
            if u1.button("📋", key=f"cp_{i}"): st.toast("ก๊อปปี้แล้ว!")
            if u2.button("🔊", key=f"sp_{i}"):
                if os.path.exists("rin_voice.mp3"): st.audio("rin_voice.mp3")

# --- 4. ส่วนรับคำสั่ง ---
audio = audio_recorder(text="กดเพื่อพูด", icon_size="2x", neutral_color="#DDA0DD")
prompt = st.chat_input("คุยกับรินได้เลยค่ะบอส...")

final_input = None
if audio:
    with st.spinner("รินกำลังฟัง..."):
        with open("t.wav", "wb") as f: f.write(audio)
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "rb") as f:
            final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text
elif prompt:
    final_input = prompt

# --- 5. การประมวลผลคำตอบ ---
if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    
    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินกำลังคิด..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "คุณคือริน เลขาบอสคิริลิ คนพัทยา ตอบฉลาดและอ้อนๆ"},
                    *st.session_state.messages
                ]
            )
            answer = chat.choices[0].message.content
            
            # สร้างเสียงเตรียมไว้
            if voice_on:
                asyncio.run(make_voice(answer))
                st.session_state.autoplay_audio = True # เปิด Flag ให้พูดอัตโนมัติหลัง rerun
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
