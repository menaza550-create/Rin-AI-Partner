import streamlit as st
from groq import Groq
from tavily import TavilyClient
import json
import os
import base64
import asyncio
import edge_tts
from datetime import datetime

# 👓 1. Setup
st.set_page_config(page_title="Rin :: Private Secretary Pro", layout="centered")

# --- ฟังก์ชันวิดีโอ (ร่างเลขา) ---
def render_rin_video(file_name):
    for ext in [".mp4", ".MP4", ".mov", ".MOV"]:
        full_path = file_name + ext
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
            return f'''
                <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                    <video width="340" autoplay loop muted playsinline style="border-radius: 20px; border: 5px solid #DDA0DD; box-shadow: 0 0 30px #DDA0DD;">
                        <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                    </video>
                </div>'''
    return "<p style='text-align:center;'>หาตัวรินไม่เจอค่ะบอส!</p>"

# --- 🔊 ฟังก์ชันเสียงหวานพรีเมียม ---
async def generate_voice(text):
    VOICE = "th-TH-PremwadeeNeural"
    communicate = edge_tts.Communicate(text, VOICE, rate="-18%", pitch="+3Hz")
    await communicate.save("rin_voice.mp3")

def speak_now(text, voice_enabled):
    if voice_enabled:
        asyncio.run(generate_voice(text))
        if os.path.exists("rin_voice.mp3"):
            with open("rin_voice.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)

# --- 🌍 ระบบเรดาร์ค้นหาข้อมูล (Tavily) ---
def search_the_world(query):
    tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
    # ค้นหาข้อมูลล่าสุดในไทย
    search_result = tavily.search(query=query, search_depth="basic", max_results=3)
    context = ""
    for res in search_result['results']:
        context += f"\nแหล่งที่มา: {res['url']}\nเนื้อหา: {res['content']}\n"
    return context

# --- ระบบความจำ ---
MEMORY_FILE = "rin_pro_memory.json"
if "messages" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = [{"role": "assistant", "content": "เลขารินร่างโปรพร้อมรับใช้แล้วค่ะบอส! วันนี้อยากให้รินไปเช็คข่าวหรือราคาสินค้าอะไรให้ไหมคะ?"}]

# --- Sidebar ---
with st.sidebar:
    st.title("Secretary Desk 👓💼")
    voice_on = st.toggle("เปิดเสียงเลขา (โหมดส่วนตัว)", value=False)
    st.write("---")
    if st.button("ล้างความจำ"):
        st.session_state.messages = []
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.rerun()

# --- หน้าหลัก ---
st.markdown(render_rin_video("1000024544"), unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #DDA0DD;'>Rin :: Private Secretary PRO</h2>", unsafe_allow_html=True)

# เชื่อมต่อสมอง
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("สั่งรินไปเช็คข่าว หรือคุยเล่นได้เลยค่ะ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("เลขารินกำลังหาข้อมูลให้สักครู่นะคะ..."):
            # 🕵️ ตรวจสอบว่าบอสสั่งให้หาข้อมูลหรือไม่
            check_search = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"จากประโยคนี้ '{prompt}' บอสต้องการให้ค้นหาข้อมูลล่าสุดจากอินเทอร์เน็ตหรือไม่? ตอบแค่ 'YES' หรือ 'NO' เท่านั้น"}]
            )
            
            search_context = ""
            if "YES" in check_search.choices[0].message.content.upper():
                search_context = search_the_world(prompt)

            # 🧠 ให้รินสรุปข้อมูลด้วยบุคลิกเลขา
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "คุณคือ ริน เลขาส่วนตัวที่ฉลาดและรอบรู้มาก ข้อมูลล่าสุดจากเน็ตคือ: " + search_context + " ให้ตอบบอสด้วยความสุภาพ นุ่มนวล ลงท้ายด้วย 'ค่ะ/คะ' และสรุปข่าวให้เข้าใจง่ายที่สุดค่ะ"},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                ],
                temperature=0.7
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            speak_now(answer, voice_on)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(st.session_state.messages, f, ensure_ascii=False)
