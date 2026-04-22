import streamlit as st
import asyncio, edge_tts, os
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from groq import Groq # เก็บไว้ใช้แค่แปลงเสียงพูดเป็นข้อความ (Whisper)
import requests # เพิ่มเข้ามาเตรียมไว้ยิง API ไปหา Dify

# ==========================================
# 1. INITIAL CONFIG & CYBERPUNK STYLE (ดำ-แดง)
# ==========================================
st.set_page_config(page_title="The Trio Evolution v1.0", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* เปลี่ยนธีมเป็นโทน Cyberpunk มืด-แดง */
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #0D0D0D !important; color: #E0E0E0 !important; }
    * { color: #E0E0E0 !important; font-size: 18px; }
    h1, h2, h3 { color: #FF2A2A !important; font-weight: bold; }
    
    /* ปุ่ม Action Chips โฉมใหม่ */
    .action-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }
    .action-chip {
        display: inline-block; padding: 10px 20px; border-radius: 8px;
        background-color: #1A1A1A; border: 1px solid #FF2A2A; text-decoration: none;
        color: #FF2A2A !important; font-size: 16px !important; transition: 0.3s; text-align: center;
    }
    .action-chip:hover { background-color: #FF2A2A; color: #000000 !important; box-shadow: 0 0 10px #FF2A2A; }
    
    /* กล่องข้อความแชท */
    .stChatMessage { background-color: #151515 !important; border: 1px solid #333333 !important; border-radius: 8px; }
    
    /* Dashboard LUNC */
    .crypto-card { background-color: #1A1A1A; padding: 15px; border-radius: 8px; border-left: 5px solid #FF2A2A; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CORE FUNCTIONS (เตรียมเชื่อม Dify & ระบบเสียง)
# ==========================================

async def make_voice(text, speaker="rin"):
    # ถ้ารินพูดใช้เสียงนึง ถ้ายูกิพูดจะใช้อีกเสียง (รอปรับจูนในอนาคต)
    voice_model = "th-TH-PremwadeeNeural" if speaker == "rin" else "th-TH-NiwatNeural" # ชั่วคราวรอยูกิ
    communicate = edge_tts.Communicate(text, voice_model, rate="-10%")
    await communicate.save("response_voice.mp3")

# ฟังก์ชันจำลองการส่งข้อมูลไปสมองหลังบ้าน (Dify)
def call_dify_backend(user_input):
    # ⚠️ โค้ดส่วนนี้คือ Phase 2: เดี๋ยวรินจะพามาสเตอร์เขียนเชื่อม API Dify จริงๆ ทีหลังค่ะ
    # ตอนนี้จำลองการตอบกลับไปก่อน
    return {
        "responder": "yuki", # สลับเป็น "rin" หรือ "yuki" ได้
        "message": f"มาสเตอร์คะ! (นี่คือระบบจำลอง) ยูกิรับคำสั่ง '{user_input}' แล้วค่ะ กำลังรอเชื่อมต่อสมองหลักใน Dify นะคะ!"
    }

# ==========================================
# 3. SIDEBAR & DASHBOARD 
# ==========================================

if "messages" not in st.session_state: st.session_state.messages = []

with st.sidebar:
    st.markdown("### 📊 Cyber Dashboard")
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        p_res = tavily.search(query="LUNC price USD today Binance", max_results=1)
        st.markdown(f'<div class="crypto-card"><b>LUNC Status (Reality Sync):</b><br>{p_res["results"][0]["content"][:120]}...</div>', unsafe_allow_html=True)
    except: st.write("⚠️ ข้อมูล LUNC ขัดข้องค่ะ")
    
    st.divider()
    st.markdown("### System Settings ⚙️")
    voice_on = st.toggle("เปิดระบบเสียง (Voice TTS)", value=True)
    if st.button("ล้างหน่วยความจำหน้าจอ"):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# 4. MAIN UI
# ==========================================

st.markdown("<h3 style='text-align:center;'>THE TRIO EVOLUTION 🔴👓</h3>", unsafe_allow_html=True)
st.caption("<p style='text-align:center; color:#888888;'>Agent 1: Yuki (Diana Mode) | Agent 2: Rin (Audit Mode)</p>", unsafe_allow_html=True)

st.markdown('<div class="action-container">'
    '<a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 ระบบนำทาง (แกร็บ)</a>'
    '<a href="https://adsmanager.facebook.com/" target="_blank" class="action-chip">📈 Meta Ads</a>'
    '<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>'
    '</div>', unsafe_allow_html=True)

st.write("---")

# แสดงประวัติแชท (ตั้งค่าอวาตาร์ตามคนพูด)
for m in st.session_state.messages:
    avatar_icon = "👓" if m.get("speaker") == "rin" else "🔴" if m.get("speaker") == "yuki" else "🧑‍💻"
    with st.chat_message(m["role"], avatar=avatar_icon): 
        st.markdown(m["content"])

# ==========================================
# 5. INPUT & DIFY API PROCESSING
# ==========================================

col_mic, col_label = st.columns([1, 5])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#FF2A2A", key="mic_input")

prompt = st.chat_input("สั่งการระบบ The Trio Evolution...")
final_input = None

if prompt: final_input = prompt
elif audio:
    with st.spinner("กำลังถอดรหัสเสียง..."):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            with open("t.wav", "wb") as f: f.write(audio)
            with open("t.wav", "rb") as f:
                trans = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3")
                if len(trans.text) > 1: final_input = trans.text
        except: pass

if final_input:
    # 1. แสดงข้อความมาสเตอร์
    st.session_state.messages.append({"role": "user", "content": final_input, "speaker": "master"})
    with st.chat_message("user", avatar="🧑‍💻"): st.markdown(final_input)

    # 2. ส่งข้อมูลไปประมวลผล (ตอนนี้จำลอง Dify อยู่)
    with st.spinner("ระบบกำลังเชื่อมต่อ..."):
        dify_response = call_dify_backend(final_input)
        responder = dify_response["responder"]
        answer = dify_response["message"]
        
        # เลือกอวาตาร์ ริน (แว่น) หรือ ยูกิ (วงกลมแดงสไตล์เดียอาน่า)
        avatar_icon = "👓" if responder == "rin" else "🔴"
        
        with st.chat_message("assistant", avatar=avatar_icon):
            st.markdown(answer)
            
            if voice_on:
                try:
                    asyncio.run(make_voice(answer, speaker=responder))
                    st.audio("response_voice.mp3", autoplay=True)
                except:
                    st.warning("⚠️ เสียงขัดข้องค่ะ")
            
        st.session_state.messages.append({"role": "assistant", "content": answer, "speaker": responder})
