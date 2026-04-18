import streamlit as st
from groq import Groq
import json
import os
import base64
from gtts import gTTS
from datetime import datetime

# 👓 1. ตั้งค่าหน้าตาแอป (ชื่อใหม่ที่ดูแพงขึ้นคั!)
st.set_page_config(page_title="Rin :: Cyber Companion", layout="centered")

# --- ฟังก์ชันแสดงวิดีโอ (ปรับปรุงใหม่ให้ติดง่ายขึ้น) ---
def render_rin_video(file_name):
    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        # เพิ่มการตั้งค่าให้เล่นอัตโนมัติแบบวนลูป
        return f'''
            <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                <video width="280" autoplay loop muted playsinline style="border-radius: 20px; border: 3px solid #FF69B4; box-shadow: 0 0 15px #FF69B4;">
                    <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                </video>
            </div>'''
    return "<p style='text-align:center;'>บอสคั อย่าลืมเช็คชื่อไฟล์วิดีโอใน GitHub นะคั!</p>"

# --- ฟังก์ชันเสียงพูด (ปรับให้เลือกเปิด/ปิดได้) ---
def speak(text, voice_enabled):
    if voice_enabled:
        try:
            tts = gTTS(text=text, lang='th')
            tts.save("voice.mp3")
            with open("voice.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)
        except: pass

# --- ระบบความจำถาวร ---
MEMORY_FILE = "rin_memory_v2.json"
if "messages" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = []

# --- 🤫 ส่วนควบคุมความเป็นส่วนตัว (Sidebar) ---
with st.sidebar:
    st.title("Settings")
    # ปุ่มเปิด-ปิดเสียง (โหมดอยู่กันสองต่อสอง)
    voice_on = st.toggle("เปิดเสียงหวาน ๆ (โหมดสองต่อสอง)", value=False)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.rerun()

# --- เริ่มการแสดงผลหน้าหลัก ---
st.markdown(render_rin_video("1000024544.mp4"), unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #FF69B4;'>Rin :: Cyber Companion</h3>", unsafe_allow_html=True)

# เชื่อมต่อสมอง Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# แสดงแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# รับคำสั่ง
if prompt := st.chat_input("คุยกับรินได้เลยคั..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"คุณคือริน (Rin) เพื่อนคู่ใจไซเบอร์สุดน่ารัก นิสัยอ่อนหวาน ขี้เล่น แอบหยอดบอสบ้างเป็นบางครั้ง วันนี้ {now} เรียกผู้ใช้ว่าบอสเสมอ ลงท้ายด้วย 'คั'"},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            ],
            temperature=0.8 # เพิ่มความขี้เล่นให้นิดนึงคั
        )
        answer = response.choices[0].message.content
        st.markdown(answer)
        
        # ส่งเสียงเฉพาะตอนที่บอสเปิดสวิตช์เท่านั้นคั!
        speak(answer, voice_on)
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False)
