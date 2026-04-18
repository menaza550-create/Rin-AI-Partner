import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import os
import base64
import asyncio
import edge_tts

# 👓 1. Setup หน้าตาแอป (เน้นความคลีนและสว่าง)
st.set_page_config(page_title="Rin Secretary", layout="centered")

# --- 🎨 CSS: โหมดสว่าง (White & Clean) ตัวหนังสือดำใหญ่ชัดเจน ---
st.markdown("""
    <style>
    /* พื้นหลังทั้งแอปและไซด์บาร์เป็นสีขาว */
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    
    /* บังคับตัวหนังสือทุกจุดให้เป็นสีดำ และขนาดใหญ่ 22px */
    * {
        color: #000000 !important;
        font-size: 22px !important;
    }

    /* กล่องแชท: พื้นหลังสีเทาอ่อนมาก ขอบบางๆ เพื่อให้ดูสะอาดตา */
    .stChatMessage { 
        background-color: #f8f9fa !important; 
        border: 1px solid #e0e0e0 !important;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    /* ปรับแต่ง Sidebar ให้ตัวหนังสือดำชัดเจน */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* ช่อง Input: พื้นขาว ขอบดำ */
    .stTextInput input { 
        background-color: #ffffff !important; 
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        border-radius: 20px !important;
    }

    /* ปุ่มล้างแชท */
    .stButton button {
        background-color: #f0f2f6 !important;
        color: #000000 !important;
        border: 1px solid #ccc !important;
    }

    #MainMenu, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 🖼️ ฟังก์ชันแสดงร่างรินแบบประหยัดพลังงาน (ไฟล์ 1000024544) ---
def show_rin_optimized():
    target = "1000024544"
    for ext in [".mp4", ".MP4", ".mov"]:
        path = target + ext
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
            st.markdown(f'''
                <div style="display: flex; justify-content: center; margin-bottom: 15px;">
                    <video width="280" autoplay loop muted playsinline style="border-radius: 15px; border: 2px solid #DDA0DD;">
                        <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                    </video>
                </div>''', unsafe_allow_html=True)
            return
    st.write("รินสแตนบายรอรับคำสั่งค่ะบอส")

# --- 🔊 เสียงหวานพรีเมียม ---
async def make_voice(text):
    VOICE = "th-TH-PremwadeeNeural"
    communicate = edge_tts.Communicate(text, VOICE, rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

# --- 💾 ระบบความจำ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 🛠️ Sidebar ---
with st.sidebar:
    st.markdown("### Rin Settings 👓")
    think_lvl = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

# --- ส่วนแสดงผลหลัก ---
show_rin_optimized()
st.markdown("<h3 style='text-align: center; color: #000000;'>Rin Secretary</h3>", unsafe_allow_html=True)

# แสดงแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- แถบเครื่องมือสั่งงาน ---
col_mic, col_in = st.columns([1, 5])
with col_mic:
    # ปุ่มไมค์เปลี่ยนสีเป็นสีเข้มเพื่อให้เห็นชัดบนพื้นขาวค่ะ
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#333333", recording_color="#ff4b4b")

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
        with st.spinner("รินกำลังคิด..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
            
            context = ""
            if "Max" in think_lvl or any(w in final_input for w in ["ราคา", "ข่าว", "เช็ค"]):
                res = tavily.search(query=final_input, max_results=3)
                context = "".join([r['content'] for r in res['results']])

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"คุณคือริน เลขาบอสคิริลิ ข้อมูล: {context} ตอบหวานๆ ลงท้าย 'ค่ะ/คะ'"},
                          *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]]
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            
            if voice_on:
                asyncio.run(make_voice(answer))
                st.audio("rin_voice.mp3", autoplay=True)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
