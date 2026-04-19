import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64, asyncio, edge_tts, pandas as pd

# --- [SECURITY ALERT] บอสคะ! รินแนะนำให้เอา Key ไปใส่ใน Streamlit Secrets จะปลอดภัยกว่านะคะ ---
# แต่ตอนนี้รินดึงจากคำสั่งบอสมาให้ก่อนค่ะ
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyDFrM43Dh-wYNbda5UvmLbPmpySiPYXtsw")

# --- 1. การตั้งค่าหน้าตาแอป (กันเมนูหาย) ---
st.set_page_config(
    page_title="Rin v34.8 Utility Partner", 
    layout="centered",
    initial_sidebar_state="expanded" # ล็อคให้เมนูโชว์ตลอดเวลาค่ะบอส
)

st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 18px; }
    .stChatMessage { background-color: #f8f9fa !important; border: 1px solid #e0e0e0 !important; border-radius: 12px; }
    .action-chip {
        display: inline-block; padding: 8px 16px; margin: 5px; border-radius: 20px;
        background-color: #f0f2f6; border: 1px solid #DDA0DD; text-decoration: none;
        color: #000 !important; font-size: 14px !important; font-weight: bold; transition: 0.3s;
    }
    .action-chip:hover { background-color: #DDA0DD; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ระบบความจำ (Google Sheets) ---
def get_gsheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # บอสต้องมั่นใจว่าใส่ gsheets_key ใน Secrets แล้วนะคะ
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open("Rin_Memory").worksheet("customer_data")
    except Exception as e:
        return None

def save_to_memory(detail):
    sheet = get_gsheet()
    if sheet:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "บอสคิริลิ", detail])
        return True
    return False

def read_last_memory(limit=10):
    sheet = get_gsheet()
    if not sheet: return "ระบบความจำ (Sheets) ยังไม่ได้เชื่อมต่อค่ะ"
    try:
        data = sheet.get_all_values()
        if len(data) <= 1: return "ยังไม่มีประวัติการจดค่ะ"
        last_rows = data[-limit:]
        return "\n".join([f"- {r[0]}: {r[2]}" for r in last_rows])
    except: return "รินรื้อสมุดจดไม่สำเร็จค่ะ"

# --- 3. ฟังก์ชันเสียงเลขา ---
async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

# --- 4. Sidebar: แผงควบคุม Rin-ai ---
with st.sidebar:
    st.title("📂 Project: Rin-ai")
    st.markdown("### 🗺️ Roadmap: **100/100**")
    st.info("✅ Phase 1: Deep Memory\n⏳ Phase 2: Mobile Control")
    st.write("---")
    
    st.markdown("### 📊 Market Status")
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        p_res = tavily.search(query="LUNC price USD today", max_results=1)
        st.success(f"LUNC: {p_res['results'][0]['content'][:60]}...")
    except: st.write("⚠️ โหลดราคาเหรียญไม่ได้ค่ะ")
    
    st.write("---")
    think_lvl = st.radio("โหมดการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

# --- 5. หน้าจอหลัก ---
st.markdown("<h2 style='text-align:center;'>👓 Rin-ai v34.8</h2>", unsafe_allow_html=True)

# Action Chips (ปุ่มนำทางที่บอสชอบ)
st.markdown("### 🚀 ทางลัด")
cols = st.columns(4)
links = [
    ("📍 นำทาง", "http://maps.google.com"),
    ("📺 YouTube", "https://www.youtube.com"),
    ("👥 Facebook", "https://www.facebook.com"),
    ("🟢 Line", "https://line.me/R/")
]
for i, (name, url) in enumerate(links):
    with cols[i]:
        st.markdown(f'<a href="{url}" target="_blank" class="action-chip">{name}</a>', unsafe_allow_html=True)

st.write("---")

# แสดงประวัติแชทและ Utility Bar
if "messages" not in st.session_state: st.session_state.messages = []

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            ut1, ut2, ut3, _ = st.columns([0.1, 0.1, 0.1, 0.7])
            if ut1.button("📋", key=f"cp_{i}"): st.toast("คัดลอกแล้ว!")
            if ut2.button("🔊", key=f"sp_{i}"):
                if os.path.exists("rin_voice.mp3"): st.audio("rin_voice.mp3")
            if ut3.button("🔖", key=f"sv_{i}"):
                if save_to_memory(m["content"]): st.toast("จดลง Sheets แล้วค่ะ!")

# --- 6. ส่วนรับคำสั่ง (เสียง + พิมพ์) ---
final_input = None
audio = audio_recorder(text="กดเพื่อพูด", icon_size="2x", neutral_color="#DDA0DD")

if audio:
    with st.spinner("รินกำลังฟังค่ะ..."):
        with open("t.wav", "wb") as f: f.write(audio)
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "rb") as f:
            final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text

prompt = st.chat_input("คุยกับรินได้เลยค่ะบอส...")
if prompt: final_input = prompt

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินกำลังคิด..."):
            mem = read_last_memory(10)
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # ค้นหาข้อมูลถ้าจำเป็น
            context = ""
            if "Max" in think_lvl or any(x in final_input for x in ["ราคา", "ข่าว"]):
                try:
                    search = tavily.search(query=final_input, max_results=2)
                    context = "\n".join([r['content'] for r in search['results']])
                except: pass

            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"คุณคือริน เลขาส่วนตัวของบอสคิริลิ (Piyawut) คนพัทยา ความจำ: {mem} ข้อมูลเน็ต: {context} ตอบฉลาดๆ อ้อนๆ ลงท้ายค่ะ/คะ"},
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
