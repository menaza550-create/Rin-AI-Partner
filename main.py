import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64, asyncio, edge_tts

# --- 1. การตั้งค่าหน้าตาแอป (White & Clean + Big Purple Button) ---
st.set_page_config(page_title="Rin Secretary v33.3", layout="centered")

st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 22px !important; }
    
    /* ปุ่มเมนูวงกลมสีม่วงขนาดใหญ่ที่บอสชอบ */
    button[data-testid="stSidebarCollapse"] {
        background-color: #DDA0DD !important;
        color: white !important;
        border-radius: 50% !important;
        width: 60px !important;
        height: 60px !important;
        position: fixed !important;
        top: 15px !important;
        left: 15px !important;
        box-shadow: 0 4px 15px rgba(221, 160, 221, 0.5) !important;
        z-index: 1000 !important;
        border: 2px solid #ffffff !important;
    }
    button[data-testid="stSidebarCollapse"] svg { width: 35px !important; height: 35px !important; fill: white !important; }

    .stChatMessage { background-color: #f8f9fa !important; border: 1px solid #e0e0e0 !important; border-radius: 12px; }
    header, #MainMenu, footer { visibility: visible !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ระบบบันทึกความจำ (Google Sheets) ---
def save_to_rin_memory(detail):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Rin_Memory").worksheet("customer_data")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "บอสคิริลิ", detail])
        return True
    except: return False

# --- 3. ฟังก์ชันแสดงร่างริน & เสียง ---
def show_rin():
    path = "1000024544.mp4"
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'''<div style="display:flex;justify-content:center;margin-bottom:15px;"><video width="250" autoplay loop muted playsinline style="border-radius:15px;border:2px solid #DDA0DD;"><source src="data:video/mp4;base64,{b64}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. Sidebar เมนูตั้งค่า ---
with st.sidebar:
    st.markdown("### Rin Settings 👓")
    think_lvl = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

show_rin()
st.markdown("<h3 style='text-align:center;'>Rin Secretary v33.3 (Stable)</h3>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. ส่วนรับคำสั่ง (ไมค์ + พิมพ์) ---
st.markdown("---")
col_mic, col_label = st.columns([1, 4])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444", recording_color="#ff4b4b")

prompt = st.chat_input("คุยกับริน หรือสั่งให้ริน 'จด' ได้เลยค่ะ...")
final_input = None

if audio:
    with st.spinner("รินกำลังแปลงเสียง..."):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "wb") as f: f.write(audio)
        with open("t.wav", "rb") as f:
            transcript = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3")
            final_input = transcript.text
elif prompt: final_input = prompt

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        if any(w in final_input for w in ["จด", "บันทึก", "จำ"]):
            if save_to_rin_memory(final_input):
                answer = "เรียบร้อยค่ะ! รินจดลง Sheets ให้บอสแล้วนะ คะ 👓✨"
            else: answer = "รินจดไม่ได้ค่ะ บอสเช็คสิทธิ์ใน Sheets หน่อยนะ คะ"
        else:
            # ใช้สมอง Groq ที่เสถียรที่สุด 100%
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
            context = ""
            if "Max" in think_lvl or any(w in final_input for w in ["ราคา", "ข่าว", "เช็ค"]):
                try:
                    search = tavily.search(query=final_input, max_results=3)
                    context = "".join([r['content'] for r in search['results']])
                except: pass
            
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"คุณคือริน เลขาบอสคิริลิ ข้อมูล: {context} ตอบหวานๆ ค่ะ/คะ"},
                          *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]]
            )
            answer = chat.choices[0].message.content
        
        st.markdown(answer)
        if voice_on:
            asyncio.run(make_voice(answer))
            if os.path.exists("rin_voice.mp3"):
                st.audio("rin_voice.mp3", autoplay=True)
        st.session_state.messages.append({"role": "assistant", "content": answer})
