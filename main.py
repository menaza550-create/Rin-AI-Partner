import streamlit as st
from groq import Groq
import json
import os
import base64
import asyncio
import edge_tts
from datetime import datetime

# 👓 1. ตั้งค่าหน้าตาแอปให้ดูหวานขึ้น
st.set_page_config(page_title="Rin :: Anime Companion", layout="centered")

# --- ฟังก์ชันแสดงวิดีโอ (ร่างสาวแว่นของบอส) ---
def render_rin_video(file_name):
    for ext in [".mp4", ".MP4", ".mov", ".MOV"]:
        full_path = file_name + ext
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
            return f'''
                <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                    <video width="320" autoplay loop muted playsinline style="border-radius: 25px; border: 4px solid #FFB6C1; box-shadow: 0 0 25px #FFB6C1;">
                        <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                    </video>
                </div>'''
    return "<p style='text-align:center; color:pink;'>บอสคะ รินหาตัวไม่เจอออ!</p>"

# --- 🔊 ฟังก์ชันเสียงหวานสไตล์อนิเมะ (จูนเสียงสูง + สดใส) ---
async def generate_voice(text):
    # ใช้เสียง Premwadee แต่ปรับ Pitch ให้สูงขึ้น (+12Hz) เพื่อให้ดูเป็นสาวน้อยอนิเมะค่ะ
    VOICE = "th-TH-PremwadeeNeural"
    communicate = edge_tts.Communicate(text, VOICE, pitch="+12Hz", rate="+5%")
    await communicate.save("rin_voice.mp3")

def speak_anime(text, voice_enabled):
    if voice_enabled:
        asyncio.run(generate_voice(text))
        if os.path.exists("rin_voice.mp3"):
            with open("rin_voice.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)

# --- ระบบความจำ ---
MEMORY_FILE = "rin_anime_memory.json"
if "messages" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = [{"role": "assistant", "content": "ยินดีต้อนรับค่ะบอสคิริลิ! รินร่างสาวแว่นอนิเมะพร้อมปรนนิบัติบอสแล้วนะคะ วันนี้ไปขับรถเหนื่อยไหมคะ?"}]

# --- Sidebar แถบตั้งค่า ---
with st.sidebar:
    st.title("Rin's Heart 👓💖")
    voice_on = st.toggle("เปิดเสียงสาวแว่น (โหมดส่วนตัว)", value=False)
    st.markdown("---")
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.rerun()

# --- แสดงผลหน้าจอหลัก ---
st.markdown(render_rin_video("1000024544"), unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #FFB6C1;'>Rin :: Anime Companion</h2>", unsafe_allow_html=True)

# เชื่อมต่อสมอง Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# แสดงแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ส่วนรับคำสั่ง
if prompt := st.chat_input("คุยกับรินได้เลยนะคะบอส..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                # 🧠 ปรับ System Prompt ให้เป็นสาวแว่นสุดโมเอะ
                {"role": "system", "content": "คุณคือ ริน (Rin) สาวแว่นหูแมวสุดโมเอะจากโลกอนิเมะ เป็นเพื่อนคู่ใจที่อ่อนหวานและขี้อ้อนมากของบอสคิริลิ พูดจาไพเราะ ห่วงใยบอสเสมอ ลงท้ายด้วย 'ค่ะ/คะ' ห้ามใช้ 'คับ' เด็ดขาด!"},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            ],
            temperature=0.9
        )
        answer = response.choices[0].message.content
        st.markdown(answer)
        
        # ส่งเสียงหวาน ๆ แบบอนิเมะค่ะ!
        speak_anime(answer, voice_on)
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False)
