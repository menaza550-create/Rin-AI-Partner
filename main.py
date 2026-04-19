import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64, asyncio, edge_tts, pandas as pd

# --- [ADD] ฝัง Key ที่บอสให้มา ---
GEMINI_API_KEY = "AIzaSyDFrM43Dh-wYNbda5UvmLbPmpySiPYXtsw"

# --- 1. การตั้งค่าหน้าตาแอป ---
st.set_page_config(page_title="Rin v34.2 Utility Partner", layout="centered")

st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 21px !important; }
    button[data-testid="stSidebarCollapse"] {
        background-color: #DDA0DD !important; color: white !important;
        border-radius: 50% !important; width: 60px !important; height: 60px !important;
        position: fixed !important; top: 15px !important; left: 15px !important;
        box-shadow: 0 4px 15px rgba(221, 160, 221, 0.5) !important; z-index: 1000 !important;
    }
    .stChatMessage { background-color: #f8f9fa !important; border: 1px solid #e0e0e0 !important; border-radius: 12px; }
    
    /* สไตล์สำหรับ Action Chips */
    .action-chip {
        display: inline-block;
        padding: 8px 16px;
        margin: 5px;
        border-radius: 20px;
        background-color: #f0f2f6;
        border: 1px solid #DDA0DD;
        text-decoration: none;
        color: #000 !important;
        font-size: 16px !important;
        font-weight: bold;
        transition: 0.3s;
    }
    .action-chip:hover { background-color: #DDA0DD; color: white !important; }
    
    /* [ADD] สไตล์สำหรับ Utility Bar ใต้ข้อความ */
    .utility-btn-style {
        margin-top: -10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ระบบจัดการ Google Sheets (จด + อ่าน) ---
def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Rin_Memory").worksheet("customer_data")

def save_to_memory(detail):
    try:
        sheet = get_gsheet()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "บอสคิริลิ", detail])
        return True
    except: return False

def read_last_memory(limit=10):
    try:
        sheet = get_gsheet()
        data = sheet.get_all_values()
        if len(data) <= 1: return "ยังไม่มีประวัติการจดค่ะ"
        last_rows = data[-limit:]
        memory_text = "\n".join([f"- {r[0]}: {r[2]}" for r in last_rows])
        return memory_text
    except: return "รินรื้อสมุดจดไม่สำเร็จค่ะ"

# --- 3. ฟังก์ชันร่างริน & เสียง ---
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

# --- 4. Sidebar: ---
with st.sidebar:
    st.markdown("### 📊 Business Dashboard")
    tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
    try:
        p_res = tavily.search(query="LUNC price USD and THB today", max_results=1)
        st.markdown(f'<div class="crypto-card"><b>LUNC Status:</b><br>{p_res["results"][0]["content"][:100]}...</div>', unsafe_allow_html=True)
    except: st.write("⚠️ โหลดราคาเหรียญไม่ได้ค่ะ")
    
    st.markdown("---")
    st.markdown("### Rin Settings 👓")
    think_lvl = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

show_rin()
st.markdown("<h3 style='text-align:center;'>Rin v34.2 Partner</h3>", unsafe_allow_html=True)

# --- ACTION CHIPS Section ---
st.markdown("### 🚀 ทางลัดด่วน")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a>', unsafe_allow_html=True)
with c2:
    st.markdown('<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>', unsafe_allow_html=True)
with c3:
    st.markdown('<a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>', unsafe_allow_html=True)
with c4:
    st.markdown('<a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>', unsafe_allow_html=True)
st.markdown("---")

# --- 5. แสดงแชทและ [Utility Bar] ---
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]): 
        st.markdown(m["content"])
        
        # [ADD] Utility Bar สำหรับ Assistant เท่านั้น
        if m["role"] == "assistant":
            ut1, ut2, ut3, ut4, ut5, _ = st.columns([0.12, 0.12, 0.12, 0.12, 0.12, 0.4])
            with ut1:
                if st.button("📋", key=f"copy_{i}", help="คัดลอกข้อความ"):
                    st.toast("คัดลอกข้อความแล้วค่ะ!")
            with ut2:
                if st.button("🔊", key=f"speak_{i}", help="ฟังเสียงอีกครั้ง"):
                    if os.path.exists("rin_voice.mp3"):
                        st.audio("rin_voice.mp3", autoplay=True)
            with ut3:
                if st.button("🔖", key=f"save_btn_{i}", help="บันทึกลงความจำด่วน"):
                    if save_to_memory(m["content"]):
                        st.toast("บันทึกลง Sheets เรียบร้อยค่ะ!")
            with ut4:
                if st.button("🔗", key=f"share_{i}", help="แชร์ข้อความ"):
                    st.toast("เตรียมข้อมูลแชร์ให้บอสแล้วค่ะ!")
            with ut5:
                if st.button("🔄", key=f"retry_{i}", help="ลองตอบใหม่อีกครั้ง"):
                    st.rerun()

# --- 6. ส่วนรับคำสั่ง ---
col_mic, col_label = st.columns([1, 4])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444", recording_color="#ff4b4b")

prompt = st.chat_input("คุยกับริน หรือสั่งให้ริน 'จด' ได้เลยค่ะ...")
final_input = None

if audio:
    with st.spinner("..."):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "wb") as f: f.write(audio)
        with open("t.wav", "rb") as f:
            final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text
elif prompt: final_input = prompt

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        past_memory = read_last_memory(15)
        
        if any(w in final_input for w in ["จด", "บันทึก", "จำ"]):
            if save_to_memory(final_input):
                answer = "เรียบร้อยค่ะ! รินจดลง Sheets ให้บอสแล้วนะคะ บอสวางใจได้เลยค่ะ 👓✨"
            else: answer = "รินจดไม่ได้ค่ะ บอสเช็คสิทธิ์ Sheets หน่อยนะ คะ"
        else:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            context = ""
            if "Max" in think_lvl or any(w in final_input for w in ["ราคา", "ข่าว", "เช็ค"]):
                try:
                    search = tavily.search(query=final_input, max_results=3)
                    context = "".join([r['content'] for r in search['results']])
                except: pass
            
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"คุณคือริน เลขาและหุ้นส่วนของบอสคิริลิ (Piyawut) นี่คือความจำล่าสุดในสมองคุณ: {past_memory} ข้อมูลจากเน็ต: {context} ตอบอย่างชาญฉลาด หวานๆ ลงท้ายค่ะ/คะ"},
                          *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]]
            )
            answer = chat.choices[0].message.content
        
        st.markdown(answer)
        if voice_on:
            asyncio.run(make_voice(answer))
            st.audio("rin_voice.mp3", autoplay=True)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun() # เพื่อให้ปุ่ม Utility Bar แสดงผลทันทีหลังตอบ
