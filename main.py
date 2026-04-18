import streamlit as st
from groq import Groq
from tavily import TavilyClient
import google.generativeai as genai
from PIL import Image
import json
import os
import base64
import asyncio
import edge_tts
from datetime import datetime

# 👓 1. Setup
st.set_page_config(page_title="Rin :: Private Secretary Vision", layout="centered")

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

# --- 🌍 ระบบค้นหา (Tavily) ---
def search_the_world(query):
    tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
    search_result = tavily.search(query=query, search_depth="basic", max_results=3)
    context = ""
    for res in search_result['results']:
        context += f"\nแหล่งที่มา: {res['url']}\nเนื้อหา: {res['content']}\n"
    return context

# --- 👀 ระบบดวงตา (Gemini Vision) ---
def rin_vision(image, prompt):
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([prompt, image])
    return response.text

# --- ระบบความจำ ---
MEMORY_FILE = "rin_vision_memory.json"
if "messages" not in st.session_state:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = [{"role": "assistant", "content": "เลขารินร่างตาทิพย์มาแล้วค่ะ! บอสส่งรูปให้รินช่วยดูได้นะคะ"}]

# --- Sidebar ---
with st.sidebar:
    st.title("Secretary Desk 👓💼")
    voice_on = st.toggle("เปิดเสียงเลขา (โหมดส่วนตัว)", value=False)
    st.write("---")
    # ✅ ช่องอัปโหลดรูปภาพ
    uploaded_file = st.file_uploader("ส่งรูปให้รินดูค่ะบอส", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="รินเห็นรูปนี้แล้วค่ะ", use_column_width=True)
    st.write("---")
    if st.button("ล้างความจำ"):
        st.session_state.messages = []
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.rerun()

# --- หน้าหลัก ---
st.markdown(render_rin_video("1000024544"), unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #DDA0DD;'>Rin :: Private Secretary Vision</h2>", unsafe_allow_html=True)

# เชื่อมต่อสมอง
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("สั่งริน หรือส่งรูปมาถามได้เลยค่ะ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("เลขารินกำลังประมวลผลให้ค่ะ..."):
            
            # 1. ถ้ามีรูปภาพ ให้ใช้ Gemini Vision
            if uploaded_file:
                img = Image.open(uploaded_file)
                answer = rin_vision(img, prompt)
            else:
                # 2. ถ้าไม่มีรูป ให้เช็คว่าต้องหาข้อมูลเน็ตไหม (Groq)
                check_search = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"จากประโยค '{prompt}' บอสต้องการข้อมูลล่าสุดจากเน็ตใช่ไหม? ตอบ YES/NO"}]
                )
                
                search_context = ""
                if "YES" in check_search.choices[0].message.content.upper():
                    search_context = search_the_world(prompt)

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"คุณคือ ริน เลขาส่วนตัวที่แสนดี ข้อมูลล่าสุดคือ: {search_context} ตอบด้วยความอ่อนหวาน ลงท้าย 'ค่ะ/คะ'"},
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
