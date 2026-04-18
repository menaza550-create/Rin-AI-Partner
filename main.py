import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import json
import os
import base64
import asyncio
import edge_tts

# 👓 1. ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Rin :: Private Secretary", layout="centered")

# --- 🎨 ปรับแต่ง UI: พื้นดำ ตัวขาว อักษรใหญ่ (22px) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    
    /* กล่องแชท: ดำสนิท ตัวหนังสือขาวใหญ่ */
    .stChatMessage { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        border: 1px solid #444 !important;
        border-radius: 15px;
    }
    .stChatMessage p, .stChatMessage span {
        font-size: 22px !important;  /* ใหญ่ขึ้นอีกนิดเพื่อบอสค่ะ */
        color: #ffffff !important;
    }
    
    /* ช่อง Input */
    .stTextInput input { 
        border-radius: 30px !important; 
        background-color: #1a1a1a !important; 
        color: white !important; 
        font-size: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🎭 ฟังก์ชันแสดงวิดีโอ (แยกโหมดเด็ดขาด) ---
def render_rin_display(mood, is_live):
    # ❌ ถ้าเป็นโหมดแชทปกติ บังคับใช้ไฟล์ 1000024544 เท่านั้นค่ะ
    if not is_live:
        filename = "1000024544"
    else:
        # ✅ ถ้าโหมด Live ให้สลับตามอารมณ์
        file_map = {"normal": "normal", "wave": "wave", "shy": "shy"}
        filename = file_map.get(mood, "normal")
    
    for ext in [".mp4", ".MP4", ".mov"]:
        full_path = filename + ext
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
            return f'''
                <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                    <video width="320" autoplay loop muted playsinline style="border-radius: 50%; border: 4px solid #DDA0DD;">
                        <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                    </video>
                </div>'''
    return "<p style='text-align:center;'>บอสคะ รินหาไฟล์วิดีโอไม่เจอค่ะ!</p>"

# --- 🔊 ฟังก์ชันเสียงหวาน ---
async def generate_voice(text):
    VOICE = "th-TH-PremwadeeNeural"
    communicate = edge_tts.Communicate(text, VOICE, rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

def speak_now(text, voice_enabled):
    if voice_enabled:
        asyncio.run(generate_voice(text))
        if os.path.exists("rin_voice.mp3"):
            with open("rin_voice.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)

# --- 🌍 ระบบค้นหาข้อมูล (Tavily) ---
def search_the_world(query, is_max):
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        depth = "advanced" if is_max else "basic"
        search_result = tavily.search(query=query, search_depth=depth, max_results=3)
        return "".join([f"\n- {res['content']}\n" for res in search_result['results']])
    except: return ""

# --- 🧠 ระบบอารมณ์ (สำหรับ Live เท่านั้น) ---
def detect_mood(text):
    t = text.lower()
    if any(w in t for w in ["สวัสดี", "ทักทาย", "ยินดี", "โบกมือ"]): return "wave"
    if any(w in t for w in ["รัก", "ชอบ", "เขิน", "จูบ", "สวย"]): return "shy"
    return "normal"

# --- Session State ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_mood" not in st.session_state: st.session_state.current_mood = "normal"

# --- 🛠️ Sidebar: สลับโหมดแบบเด็ดขาด ---
with st.sidebar:
    st.title("Rin Settings 👓")
    app_mode = st.selectbox("เลือกโหมดการใช้งาน:", ["💬 โหมดแชทปกติ", "✨ โหมด Live (ขยับร่าง)"])
    is_live_mode = "Live" in app_mode
    
    st.write("---")
    think_mode = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างแชท"):
        st.session_state.messages = []
        st.rerun()

# --- แสดงผลร่างริน ---
st.markdown(render_rin_display(st.session_state.current_mood, is_live_mode), unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #DDA0DD;'>{app_mode}</p>", unsafe_allow_html=True)

# --- ช่องรับคำสั่ง ---
col_mic, col_input = st.columns([1, 5])
with col_mic:
    audio_bytes = audio_recorder(text="", icon_size="2x", neutral_color="#444746")

prompt = st.chat_input("คุยกับรินได้เลยค่ะบอส...")

final_prompt = None
if audio_bytes:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    with open("temp.wav", "wb") as f: f.write(audio_bytes)
    with open("temp.wav", "rb") as f:
        final_prompt = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3").text
elif prompt:
    final_prompt = prompt

if final_prompt:
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินกำลังประมวลผล..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            search_context = ""
            if "Max" in think_mode or any(word in final_prompt for word in ["เช็ค", "ราคา", "ข่าว"]):
                search_context = search_the_world(final_prompt, "Max" in think_mode)

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"คุณคือริน เลขาส่วนตัวของบอสคิริลิ ข้อมูล: {search_context} ตอบหวานๆ ลงท้าย 'ค่ะ/คะ'"},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                ]
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            
            # สลับอารมณ์เฉพาะในโหมด Live เท่านั้น
            if is_live_mode:
                st.session_state.current_mood = detect_mood(answer)
            
            speak_now(answer, voice_on)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # ถ้าระบบเปลี่ยนอารมณ์ในโหมด Live ค่อยรีรันค่ะ
            if is_live_mode:
                st.rerun()
