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

# --- ฟังก์ชันแสดงวิดีโอ (ตรวจเช็คไฟล์ละเอียดขึ้นคับ) ---
def render_rin_video(file_name):
    # ตรวจสอบนามสกุลไฟล์ที่บอสน่าจะใช้
    valid_exts = [".mp4", ".MP4", ".mov", ".MOV", ".m4v"]
    found_file = None
    for ext in valid_exts:
        full_path = file_name + ext
        if os.path.exists(full_path):
            found_file = full_path
            break
            
    if found_file:
        with open(found_file, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        return f'''
            <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                <video width="320" autoplay loop muted playsinline style="border-radius: 20px; border: 3px solid #FF69B4; box-shadow: 0 0 15px #FF69B4;">
                    <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                </video>
            </div>'''
    
    # ถ้าหาไม่เจอ รินจะแจ้งบอสแบบสุภาพคับ
    return f"""<div style='text-align:center; padding:20px; border:2px dashed #ccc; border-radius:15px;'>
                <p style='color:red; font-weight:bold;'>บอสคับ รินหาไฟล์ {file_name}.mp4 ใน GitHub ไม่เจอคับ!</p>
                <p style='color:gray; font-size:0.8em;'>เช็คชื่อไฟล์บน GitHub อีกทีนะคับ (ต้องไม่มีเว้นวรรค) <br>
                และขนาดไฟล์ต้องไม่ใช่ 2 Bytes คับบอส!</p>
               </div>"""

# --- 🔊 ฟังก์ชันเสียงหวาน (จูนความเร็วให้นุ่มนวลคับ) ---
async def generate_voice(text):
    VOICE = "th-TH-PremwadeeNeural"
    communicate = edge_tts.Communicate(text, VOICE, rate="-10%")
    await communicate.save("rin_voice.mp3")

def speak_now(text, voice_enabled):
    if voice_enabled:
        asyncio.run(generate_voice(text))
        if os.path.exists("rin_voice.mp3"):
            with open("rin_voice.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)

# --- ระบบความจำถาวร ---
MEMORY_FILE = "rin_memory_v85.json"
if "messages" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
    else:
        # เปลี่ยนเป็น คับ แล้วคับ!
        st.session_state.messages = [{"role": "assistant", "content": "รินร่างสมบูรณ์พร้อมปรนนิบัติบอสแล้วคับ! วันนี้เหนื่อยไหมคับ?"}]

# --- Sidebar แถบตั้งค่า ---
with st.sidebar:
    st.title("Rin Settings 👓")
    voice_on = st.toggle("เปิดเสียงหวาน (โหมดสองต่อสอง)", value=False)
    st.markdown("---")
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.rerun()

# --- แสดงผลหน้าจอหลัก ---
st.markdown(render_rin_video("1000024544"), unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #FF69B4;'>Rin :: My Cyber Companion</h3>", unsafe_allow_html=True)

# เชื่อมต่อสมอง Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# แสดงแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ส่วนรับคำสั่ง
if prompt := st.chat_input("คุยกับรินร่างที่บอสเลือกเลยคับ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                # เน้นย้ำให้ใช้ "คับ" ในสมองรินด้วยคับ!
                {"role": "system", "content": "คุณคือ ริน (Rin) หูแมวใส่แว่น เป็นเพื่อนคู่ใจที่ขี้อ้อนและฉลาดมากของบอสคิริลิ ชวนคุยเก่ง ให้กำลังใจบอสเสมอ ห้ามใช้ 'คั' ให้ใช้ 'คับ' ทุกประโยค ห้ามยกเว้น!"},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            ],
            temperature=0.8
        )
        answer = response.choices[0].message.content
        st.markdown(answer)
        
        # พูดด้วยเสียงหวานๆ คับ!
        speak_now(answer, voice_on)
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False)
