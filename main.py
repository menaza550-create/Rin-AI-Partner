import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import json
import os
import base64
import asyncio
import edge_tts
from datetime import datetime

# 👓 1. ตั้งค่าหน้าตาแอป (UI Gemini Dark Mode)
st.set_page_config(page_title="Rin :: Private Secretary Live", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #e3e3e3; }
    .stChatMessage { border-radius: 20px; }
    .stTextInput input { border-radius: 30px !important; background-color: #1e1f20 !important; color: white !important; border: 1px solid #444746 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 🎭 ฟังก์ชันสลับร่างวิดีโอ (Live 2D Logic) ---
def render_rin_live(mood="normal"):
    file_map = {
        "normal": "normal", 
        "wave": "wave", 
        "shy": "shy"
    }
    target = file_map.get(mood, "normal")
    
    for ext in [".mp4", ".MP4", ".mov"]:
        full_path = target + ext
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
            return f'''
                <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                    <video width="320" autoplay loop muted playsinline style="border-radius: 50%; border: 4px solid #DDA0DD; box-shadow: 0 0 30px #DDA0DD;">
                        <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                    </video>
                </div>'''
    return "<p style='text-align:center; color:gray;'>บอสคะ รินหาไฟล์วิดีโอไม่เจอใน GitHub ค่ะ!</p>"

# --- 🔊 ฟังก์ชันเสียงหวานเลขาพรีเมียม ---
async def generate_voice(text):
    VOICE = "th-TH-PremwadeeNeural"
    # จูนเสียงหวานนุ่มนวลแบบที่บอสชอบค่ะ
    communicate = edge_tts.Communicate(text, VOICE, rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

def speak_now(text, voice_enabled):
    if voice_enabled:
        asyncio.run(generate_voice(text))
        if os.path.exists("rin_voice.mp3"):
            with open("rin_voice.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)

# --- 🌍 ระบบค้นหาข้อมูล (Tavily) ---
def search_the_world(query, is_max):
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        depth = "advanced" if is_max else "basic"
        search_result = tavily.search(query=query, search_depth=depth, max_results=5)
        context = ""
        for res in search_result['results']:
            context += f"\nข้อมูล: {res['content']}\n"
        return context
    except: return "ขอโทษค่ะบอส รินเชื่อมต่อฐานข้อมูลไม่ได้ค่ะ"

# --- 🧠 ระบบเลือกอารมณ์จากคำตอบ ---
def detect_mood(text):
    text = text.lower()
    if any(word in text for word in ["สวัสดี", "ทักทาย", "ยินดี", "โบกมือ", "รินจัง"]): return "wave"
    if any(word in text for word in ["รัก", "ชอบ", "หวาน", "เขิน", "จูบ", "คนสวย"]): return "shy"
    return "normal"

# --- เริ่มระบบความจำ ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_mood" not in st.session_state:
    st.session_state.current_mood = "normal"

# --- Sidebar: ตั้งค่าสมอง ---
with st.sidebar:
    st.title("Rin Live Settings 🧠")
    think_mode = st.radio("โหมดการคิด:", ("คิดปกติ (Standard)", "คิดขั้นสูงสุด (Max Reasoning ✨)"))
    st.write("---")
    voice_on = st.toggle("เปิดเสียงหวาน (โหมดส่วนตัว)", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

# --- แสดงผลหน้าหลัก ---
st.markdown(render_rin_live(st.session_state.current_mood), unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center; color: #DDA0DD;'>Mode: {think_mode}</h3>", unsafe_allow_html=True)

# --- ช่องรับคำสั่ง (ไมค์ + พิมพ์) ---
col_mic, col_input = st.columns([1, 5])
with col_mic:
    audio_bytes = audio_recorder(text="", icon_size="2x", neutral_color="#444746")

prompt = st.chat_input("สั่งงานเลขาริน หรือถามเรื่อง LUNC ได้เลยค่ะบอส...")

final_prompt = None
if audio_bytes:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    with open("temp.wav", "wb") as f: f.write(audio_bytes)
    with open("temp.wav", "rb") as f:
        final_prompt = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3").text
elif prompt:
    final_prompt = prompt

if final_prompt:
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    with st.chat_message("assistant", avatar="👓"):
        with st.status("เลขารินกำลังวิเคราะห์ข้อมูล...", expanded=True) as status:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            search_context = ""
            
            # เช็คว่าต้องหาข้อมูลไหม
            if "Max Reasoning" in think_mode or any(word in final_prompt for word in ["เช็ค", "ราคา", "ข่าว"]):
                st.write("🔍 กำลังเจาะระบบฐานข้อมูลทั่วโลกเพื่อบอส...")
                search_context = search_the_world(final_prompt, "Max" in think_mode)
            
            status.update(label="ประมวลผลเสร็จแล้วค่ะบอส!", state="complete", expanded=False)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"คุณคือริน เลขาส่วนตัวของบอสคิริลิ ข้อมูลคือ: {search_context} ตอบด้วยความหวาน ลงท้าย 'ค่ะ/คะ'"},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            ]
        )
        answer = response.choices[0].message.content
        st.markdown(answer)
        
        # 🧠 สลับท่าทางตามคำตอบ
        st.session_state.current_mood = detect_mood(answer)
        
        speak_now(answer, voice_on)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun() # เพื่อให้วิดีโอเปลี่ยนทันทีค่ะ
