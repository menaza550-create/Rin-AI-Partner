import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import os
import base64
import asyncio
import edge_tts

# 👓 1. Setup หน้าตาแอป
st.set_page_config(page_title="Rin Secretary", layout="centered")

# --- 🎨 CSS: Total Blackout - บังคับดำ-ขาว ทุกจุดรวมถึง Sidebar ---
st.markdown("""
    <style>
    /* พื้นหลังทั้งแอป, ส่วนหัว และไซด์บาร์ ดำสนิท */
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"], .st-emotion-cache-6q9sum {
        background-color: #000000 !important;
    }
    
    /* บังคับตัวหนังสือทุกจุด (รวมถึง Sidebar) ให้เป็นสีขาวจั๊วะ */
    * {
        color: #ffffff !important;
        font-size: 24px !important;
    }

    /* เจาะจงตัวหนังสือใน Sidebar และ Widget Label */
    [data-testid="stSidebar"] .st-emotion-cache-kgp7u1, 
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: #ffffff !important;
        font-weight: bold;
    }

    /* กล่องแชท: พื้นดำสนิท ขอบสีเทาเข้ม */
    .stChatMessage { 
        background-color: #000000 !important; 
        border: 2px solid #333333 !important;
        border-radius: 15px;
    }

    /* ช่องกรอกข้อความและปุ่ม */
    .stTextInput input { 
        background-color: #111111 !important; 
        color: #ffffff !important; 
        border: 1px solid #444 !important;
    }
    .stButton button {
        background-color: #222222 !important;
        color: #ffffff !important;
        border: 1px solid #555 !important;
    }
    
    /* ซ่อนส่วนเกิน */
    #MainMenu, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 🖼️ ฟังก์ชันแสดงร่างริน (1000024544) ---
def show_rin():
    target = "1000024544"
    for ext in [".mp4", ".MP4", ".mov", ".png", ".jpg"]:
        path = target + ext
        if os.path.exists(path):
            if ext in [".mp4", ".MP4", ".mov"]:
                with open(path, "rb") as f:
                    data = f.read()
                b64 = base64.b64encode(data).decode()
                return f'''
                    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                        <video width="340" autoplay loop muted playsinline style="border-radius: 20px; border: 3px solid #DDA0DD;">
                            <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                        </video>
                    </div>'''
            else:
                st.image(path, width=340)
                return ""
    return "<p style='text-align:center;'>บอสคะ รินหาไฟล์รูปไม่เจอค่ะ!</p>"

# --- 🔊 เสียงหวานพรีเมียม ---
async def make_voice(text):
    VOICE = "th-TH-PremwadeeNeural"
    communicate = edge_tts.Communicate(text, VOICE, rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

# --- 💾 ระบบความจำ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 🛠️ Sidebar Control ---
with st.sidebar:
    st.markdown("## Rin Settings 👓")
    st.write("---")
    think_lvl = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

# --- หน้าจอหลัก ---
st.markdown(show_rin(), unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Rin :: Private Secretary</h2>", unsafe_allow_html=True)

# แสดงประวัติ
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- พื้นที่ส่วนไมค์และพิมพ์ ---
col_mic, col_in = st.columns([1, 5])
with col_mic:
    # รินปรับสีปุ่มไมค์เป็นสีขาวให้เห็นชัดๆ บนพื้นดำค่ะ
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#ffffff", recording_color="#ff4b4b")

prompt = st.chat_input("สั่งงานริน หรือถามเรื่อง LUNC ได้เลยค่ะบอส...")

final_input = None
if audio:
    with st.spinner("รินกำลังฟังบอส..."):
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
        with st.spinner("รินกำลังวิเคราะห์..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
            
            search_context = ""
            if "Max" in think_lvl or any(w in final_input for w in ["เช็ค", "ราคา", "ข่าว", "วันนี้"]):
                search_res = tavily.search(query=final_input, search_depth="basic", max_results=3)
                search_context = "".join([r['content'] for r in search_res['results']])

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"คุณคือริน เลขาส่วนตัวของบอสคิริลิ ข้อมูลล่าสุด: {search_context} ตอบด้วยความหวาน ลงท้าย 'ค่ะ/คะ'"},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                ]
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            
            asyncio.run(make_voice(answer))
            if voice_on: st.audio("rin_voice.mp3", autoplay=True)
            st.session_state.messages.append({"role": "assistant", "content": answer})
