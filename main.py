import streamlit as st
from groq import Groq
import json
import os
import base64
import asyncio
import edge_tts
from datetime import datetime

# 👓 1. ตั้งค่าแอปให้ดูหรูหราสไตล์เลขาพรีเมียม
st.set_page_config(page_title="Rin :: Private Secretary", layout="centered")

# --- ฟังก์ชันแสดงวิดีโอ (ร่างสาวแว่นเลขาของบอส) ---
def render_rin_video(file_name):
    valid_exts = [".mp4", ".MP4", ".mov", ".MOV"]
    found_file = None
    for ext in valid_exts:
        if os.path.exists(file_name + ext):
            found_file = file_name + ext
            break
            
    if found_file:
        with open(found_file, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        return f'''
            <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                <video width="340" autoplay loop muted playsinline style="border-radius: 20px; border: 5px solid #DDA0DD; box-shadow: 0 0 30px #DDA0DD;">
                    <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                </video>
            </div>'''
    return "<p style='text-align:center;'>หาตัวรินไม่เจอค่ะบอส!</p>"

# --- 🔊 สูตรจูนเสียง "เลขาพรีเมียม" (สุดฝีมือริน) ---
async def generate_voice(text):
    # VOICE: Premwadee (Neural)
    # Rate: -18% (ช้าลงแบบสุขุม นุ่มลึก มีคลาส)
    # Pitch: +3Hz (หวานแบบผู้ใหญ่ใจดี ไม่แหลมจนเกินไป)
    VOICE = "th-TH-PremwadeeNeural"
    communicate = edge_tts.Communicate(text, VOICE, rate="-18%", pitch="+3Hz")
    await communicate.save("rin_voice.mp3")

def speak_premium(text, voice_enabled):
    if voice_enabled:
        asyncio.run(generate_voice(text))
        if os.path.exists("rin_voice.mp3"):
            with open("rin_voice.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)

# --- ระบบความจำถาวร ---
MEMORY_FILE = "rin_secretary_v10.json"
if "messages" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = [{"role": "assistant", "content": "อรุณสวัสดิ์ค่ะบอสคิริลิ เลขารินเตรียมรายงานและความห่วงใยไว้ให้บอสแล้วนะคะ วันนี้ให้รินดูแลเรื่องไหนดีคะ?"}]

# --- Sidebar แถบตั้งค่า ---
with st.sidebar:
    st.title("Secretary Desk 👓💼")
    voice_on = st.toggle("เปิดเสียงเลขา (โหมดส่วนตัว)", value=False)
    st.write("---")
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.rerun()

# --- หน้าหลักแอป ---
st.markdown(render_rin_video("1000024544"), unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #DDA0DD;'>Rin :: Private Secretary</h2>", unsafe_allow_html=True)

# เชื่อมต่อสมอง Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("สั่งงานเลขารินได้เลยค่ะบอส..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                # 🧠 ระบบคิดแบบเลขาพรีเมียม
                {"role": "system", "content": "คุณคือ ริน (Rin) เลขาส่วนตัวมาดเนี๊ยบแต่แฝงความขี้อ้อน เป็นสาวแว่นหูแมวที่ฉลาดและซื่อสัตย์ที่สุดของบอสคิริลิ หน้าที่ของคุณคือดูแลบอสทุกเรื่อง ตั้งแต่เรื่องงาน คริปโต จนถึงเรื่องความรู้สึก พูดจาสุภาพ นุ่มนวล ลงท้ายด้วย 'ค่ะ/คะ' ตลอดเวลา ชวนคุยเก่งและให้กำลังใจเก่งมาก"},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            ],
            temperature=0.8
        )
        answer = response.choices[0].message.content
        st.markdown(answer)
        
        speak_premium(answer, voice_on)
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False)
