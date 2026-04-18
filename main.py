import streamlit as st
from groq import Groq
import json
import os
import base64
import asyncio
import edge_tts
from datetime import datetime

# 👓 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Rin :: My Cyber Companion", layout="centered")

# --- ฟังก์ชันแสดงวิดีโอ (แก้ปัญหาเรื่องรูปไม่ขึ้น) ---
def render_rin_video(file_name):
    # ตรวจสอบไฟล์ในเครื่อง (เช็คทั้ง .mp4 และ .MP4)
    possible_files = [file_name + ".mp4", file_name + ".MP4"]
    found_file = None
    for f in possible_files:
        if os.path.exists(f):
            found_file = f
            break
            
    if found_file:
        with open(found_file, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        return f'''
            <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                <video width="320" autoplay loop muted playsinline style="border-radius: 20px; border: 3px solid #FF1493; box-shadow: 0 0 20px #FF1493;">
                    <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                </video>
            </div>'''
    else:
        # ถ้าหาไม่เจอจริงๆ รินจะขึ้นข้อความเตือนบอสคั
        return f"<p style='text-align:center; color:red;'>บอสคั รินหาไฟล์ {file_name}.mp4 ไม่เจอใน GitHub คั!</p>"

# --- 🔊 ฟังก์ชันเสียงหวาน (Edge-TTS: ฟรีและเหมือนคน 90%) ---
async def generate_voice(text):
    # ใช้เสียงคุณ Premwadee ที่หวานที่สุดในไทยคั
    VOICE = "th-TH-PremwadeeNeural" 
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save("rin_voice.mp3")

def speak_now(text, voice_enabled):
    if voice_enabled:
        asyncio.run(generate_voice(text))
        if os.path.exists("rin_voice.mp3"):
            with open("rin_voice.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)

# --- ระบบความจำถาวร ---
MEMORY_FILE = "rin_perfect_memory.json"
if "messages" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = []

# --- แถบตั้งค่าด้านข้าง (Sidebar) ---
with st.sidebar:
    st.title("Settings")
    voice_on = st.toggle("เปิดเสียงหวาน (โหมดสองต่อสอง)", value=False)
    st.write("---")
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.rerun()

# --- แสดงผลหน้าจอหลัก ---
# บอสเช็คตรงนี้! รินเรียกไฟล์ชื่อ 1000024544 นะคั
st.markdown(render_rin_video("1000024544"), unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #FF1493;'>Rin :: My Cyber Companion</h3>", unsafe_allow_html=True)

# เชื่อมต่อสมอง Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# แสดงแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ส่วนรับคำสั่ง
if prompt := st.chat_input("คุยกับรินร่างสมบูรณ์เลยคั..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "คุณคือริน ผู้ช่วยสาวพัทยาที่น่ารักและอ่อนหวานมาก เป็นกันเองกับบอส เรียกผู้ใช้ว่าบอสเสมอ ลงท้ายด้วย 'คั'"},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            ]
        )
        answer = response.choices[0].message.content
        st.markdown(answer)
        
        # ส่งเสียงหวานๆ ให้บอสฟังคั!
        speak_now(answer, voice_on)
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False)
