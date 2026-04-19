import streamlit as st
from groq import Groq
import json
import os
import base64
from gtts import gTTS
from datetime import datetime

# 👓 ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Rin AI v5/5", layout="centered")

# --- ฟังก์ชันแสดงวิดีโอขยับได้ ---
def render_rin_video(file_name):
    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        return f'''
            <div style="display: flex; justify-content: center;">
                <video width="260" autoplay loop muted style="border-radius: 50%; border: 4px solid #00BFFF; box-shadow: 0 0 20px #00BFFF;">
                    <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                </video>
            </div>'''
    return "<p style='text-align:center;'>บอสคั อย่าลืมอัปโหลดไฟล์วิดีโอขึ้น GitHub นะคั!</p>"

# --- ฟังก์ชันเสียงพูดภาษาไทย ---
def speak(text):
    try:
        tts = gTTS(text=text, lang='th')
        tts.save("voice.mp3")
        with open("voice.mp3", "rb") as f:
            st.audio(f.read(), format="audio/mp3", autoplay=True)
    except: pass

# --- ระบบความจำถาวร ---
MEMORY_FILE = "memory.json"
if "messages" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = []

# --- เริ่มการแสดงผล ---
st.markdown(render_rin_video("1000024544.mp4"), unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>👓 น้องริน เสมียนพัทยา</h3>", unsafe_allow_html=True)

# เชื่อมต่อสมอง Groq (ดึงรหัสลับจาก Secrets)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# แสดงแชทเก่า
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ส่วนรับคำสั่ง
if prompt := st.chat_input("คุยกับรินเลยคับอส..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        # 🚀 ใช้สมอง Llama 3.3 70B ตัวเทพ
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"คุณคือริน ผู้ช่วยสาวพัทยา หูแมวใส่แว่น ขี้เล่น สุภาพ วันนี้ {now} เรียกผู้ใช้ว่าบอส ลงท้าย 'คั'"},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            ]
        )
        answer = response.choices[0].message.content
        st.markdown(answer)
        speak(answer) # พ่นเสียงออกมา
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        # เซฟความจำ
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False)
