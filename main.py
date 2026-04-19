import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64, asyncio, edge_tts, pandas as pd

# --- [SETTING] ตั้งค่าหน้าตาแอป (บังคับให้เมนูโชว์) ---
st.set_page_config(
    page_title="Rin v34.8 Utility Partner", 
    layout="centered",
    initial_sidebar_state="expanded" 
)

# สไตล์ตกแต่ง (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 18px !important; }
    .stChatMessage { border-radius: 12px; border: 1px solid #eee; margin-bottom: 10px; }
    .action-chip {
        display: inline-block; padding: 8px 16px; margin: 5px; border-radius: 20px;
        background-color: #f0f2f6; border: 1px solid #DDA0DD; text-decoration: none;
        color: #000 !important; font-size: 14px !important; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. ระบบความจำ (Google Sheets) ---
def get_gsheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open("Rin_Memory").worksheet("customer_data")
    except: return None

def save_to_memory(detail):
    sheet = get_gsheet()
    if sheet:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([now, "บอสคิริลิ", detail])
            return True
        except: return False
    return False

def read_last_memory(limit=10):
    sheet = get_gsheet()
    if not sheet: return "ระบบจำ (Sheets) ยังไม่ได้ต่อค่ะ"
    try:
        data = sheet.get_all_values()
        if len(data) <= 1: return "ยังไม่มีประวัติจดค่ะ"
        return "\n".join([f"- {r[0]}: {r[2]}" for r in data[-limit:]])
    except: return "รื้อสมุดจดไม่สำเร็จค่ะ"

# --- 2. ฟังก์ชันเสียงเลขา ---
async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

# --- 3. SIDEBAR (แผงควบคุม) ---
with st.sidebar:
    st.title("📂 Project: Rin-ai")
    st.markdown("### 🗺️ Roadmap: **100/100**")
    st.info("✅ Phase 1: Deep Memory\n⏳ Phase 2: Mobile Control")
    st.divider()
    
    # ตรวจสอบ API Keys จาก Secrets
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        st.success("Tavily: Online 🔍")
    except: st.error("Tavily: Key Missing ❌")

    think_lvl = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

# --- 4. หน้าจอหลัก ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v34.8 Partner</h2>", unsafe_allow_html=True)

# Action Chips (ทางลัดที่บอสชอบ)
st.markdown("### 🚀 ทางลัด")
cols = st.columns(4)
btn_info = [
    ("📍 นำทาง", "http://maps.google.com"),
    ("📺 YouTube", "https://www.youtube.com"),
    ("👥 Facebook", "https://www.facebook.com"),
    ("🟢 Line", "https://line.me/R/")
]
for i, (name, url) in enumerate(btn_info):
    with cols[i]:
        st.markdown(f'<a href="{url}" target="_blank" class="action-chip">{name}</a>', unsafe_allow_html=True)

st.write("---")

# จัดการ Session State
if "messages" not in st.session_state: st.session_state.messages = []

# แสดงแชทและ Utility Bar
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            u1, u2, u3, _ = st.columns([0.1, 0.1, 0.1, 0.7])
            if u1.button("📋", key=f"cp_{i}"): st.toast("ก๊อปปี้แล้ว!")
            if u2.button("🔊", key=f"sp_{i}"): 
                if os.path.exists("rin_voice.mp3"): st.audio("rin_voice.mp3")
            if u3.button("🔖", key=f"sv_{i}"):
                if save_to_memory(m["content"]): st.toast("จดลง Sheets แล้ว!")

# --- 5. ส่วนรับคำสั่ง (STT + พิมพ์) ---
audio = audio_recorder(text="กดเพื่อพูด", icon_size="2x", neutral_color="#DDA0DD")
prompt = st.chat_input("คุยกับริน หรือสั่งให้ริน 'จด' ได้เลยค่ะ...")

final_input = None
if audio:
    with st.spinner("รินกำลังฟัง..."):
        with open("t.wav", "wb") as f: f.write(audio)
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "rb") as f:
            final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text
elif prompt:
    final_input = prompt

# --- 6. การประมวลผลคำตอบ ---
if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินกำลังประมวลผล..."):
            past_mem = read_last_memory(15)
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # ตรวจสอบการค้นหาข้อมูล
            context = ""
            if "Max" in think_lvl or any(w in final_input for w in ["ราคา", "ข่าว", "เช็ค"]):
                try:
                    search = tavily.search(query=final_input, max_results=2)
                    context = "\n".join([r['content'] for r in search['results']])
                except: pass

            # ตอบคำถาม
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"คุณคือริน เลขาบอสคิริลิ (Piyawut) คนพัทยา จำไว้ว่า: {past_mem} ข้อมูลใหม่: {context} ตอบอย่างชาญฉลาดและอ้อนๆ ลงท้ายค่ะ/คะ"},
                    *st.session_state.messages
                ]
            )
            answer = chat.choices[0].message.content
            st.markdown(answer)

            if voice_on:
                asyncio.run(make_voice(answer))
                st.audio("rin_voice.mp3", autoplay=True)

            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
