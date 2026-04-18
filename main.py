import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import os
import base64
import asyncio
import edge_tts

# 👓 1. Setup หน้าตาแอป (เน้นความชัดเจนและเสถียรที่สุด)
st.set_page_config(page_title="Rin :: Private Secretary", layout="centered")

# --- 🎨 CSS: บังคับดำสนิท-ขาวสว่าง ทุกตารางนิ้ว ---
st.markdown("""
    <style>
    /* พื้นหลังทั้งแอปดำสนิท */
    .stApp { background-color: #000000; color: #ffffff; }
    
    /* บังคับตัวหนังสือทุกจุดให้เป็นสีขาวและใหญ่ขึ้น */
    html, body, [class*="st-"] {
        color: #ffffff !important;
        font-size: 24px !important;
        font-family: 'Inter', sans-serif;
    }

    /* กล่องแชท: ดำสนิท ขอบเทา ตัวหนังสือขาวจั๊วะ */
    .stChatMessage { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        border: 2px solid #333333 !important;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
    }
    
    /* ป้ายชื่อและ Label ต่างๆ ใน Sidebar และหน้าจอ */
    label, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ffffff !important;
        font-size: 24px !important;
    }

    /* ช่องกรอกข้อความ */
    .stTextInput input { 
        background-color: #1a1a1a !important; 
        color: #ffffff !important; 
        font-size: 22px !important;
        border-radius: 25px !important;
    }

    /* ปุ่มกด */
    .stButton button {
        background-color: #333333 !important;
        color: #ffffff !important;
        border-radius: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🖼️ ฟังก์ชันแสดงร่างริน (ล็อคไฟล์ 1000024544) ---
def render_rin_static():
    filename = "1000024544" # ล็อคไว้ที่ไฟล์นี้ตามสั่งค่ะบอส
    for ext in [".mp4", ".MP4", ".mov", ".png", ".jpg"]:
        path = filename + ext
        if os.path.exists(path):
            if ext in [".mp4", ".MP4", ".mov"]:
                with open(path, "rb") as f:
                    data = f.read()
                b64 = base64.b64encode(data).decode()
                return f'''
                    <div style="display: flex; justify-content: center; margin-bottom: 25px;">
                        <video width="350" autoplay loop muted playsinline style="border-radius: 20px; border: 4px solid #DDA0DD;">
                            <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                        </video>
                    </div>'''
            else:
                st.image(path, width=350)
                return ""
    return "<p style='text-align:center; color:white;'>บอสคะ รินหาไฟล์ 1000024544 ไม่เจอค่ะ!</p>"

# --- 🔊 เสียงหวานพรีเมียม ---
async def generate_voice(text):
    VOICE = "th-TH-PremwadeeNeural"
    communicate = edge_tts.Communicate(text, VOICE, rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

# --- 💾 ระบบความจำ ---
if "messages" not in st.session_state: st.session_state.messages = []

# --- 🛠️ Sidebar: ตั้งค่าแบบง่าย ---
with st.sidebar:
    st.markdown("### Rin Control Center 👓")
    st.write("---")
    think_lvl = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติแชท"):
        st.session_state.messages = []
        st.rerun()

# --- แสดงผลหน้าหลัก ---
st.markdown(render_rin_static(), unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #ffffff;'>Rin :: Private Secretary</h2>", unsafe_allow_html=True)

# --- แสดงประวัติแชท ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- ส่วนรับคำสั่ง ---
col_mic, col_in = st.columns([1, 5])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#ffffff")

prompt = st.chat_input("คุยกับเลขารินได้เลยค่ะบอส...")

final_input = None
if audio:
    with st.spinner("รินกำลังฟัง..."):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "wb") as f: f.write(audio)
        with open("t.wav", "rb") as f:
            final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text
elif prompt:
    final_input = prompt

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินกำลังหาข้อมูล..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
            
            context = ""
            if "Max" in think_lvl or any(w in final_input for w in ["เช็ค", "ราคา", "ข่าว"]):
                search = tavily.search(query=final_input, search_depth="basic", max_results=3)
                context = "".join([r['content'] for r in search['results']])

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"คุณคือริน เลขาบอสคิริลิ ข้อมูลคือ: {context} ตอบหวานๆ ลงท้าย 'ค่ะ/คะ'"},
                          *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]]
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            
            asyncio.run(generate_voice(answer))
            if voice_on: st.audio("rin_voice.mp3", autoplay=True)
            st.session_state.messages.append({"role": "assistant", "content": answer})
