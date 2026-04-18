import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64, asyncio, edge_tts

# 👓 1. Setup หน้าตาแอป (White & Clean Edition)
st.set_page_config(page_title="Rin Secretary v33.0", layout="centered")

# --- 🎨 CSS: บังคับให้เมนูอยู่ครบ ตัวหนังสือดำชัดเจน ---
st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 22px !important; }
    
    /* บังคับให้เมนู 3 ขีดและ Sidebar แสดงผลชัดเจน */
    header[data-testid="stHeader"] { visibility: visible !important; background-color: #ffffff !important; }
    #MainMenu { visibility: visible !important; color: #000000 !important; }
    
    .stChatMessage { background-color: #f8f9fa !important; border: 1px solid #e0e0e0 !important; border-radius: 12px; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #000000 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 🧠 2. ฟังก์ชันระบบความจำ (Google Sheets) ---
def save_to_rin_memory(detail):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Rin_Memory").worksheet("customer_data")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "บอสคิริลิ", detail])
        return True
    except Exception as e:
        st.error(f"รินจดไม่ได้ค่ะบอส: {e}")
        return False

# --- 🖼️ 3. ฟังก์ชันแสดงร่างริน ---
def show_rin():
    path = "1000024544.mp4"
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'''<div style="display: flex; justify-content: center; margin-bottom: 15px;"><video width="260" autoplay loop muted playsinline style="border-radius: 15px; border: 2px solid #DDA0DD;"><source src="data:video/mp4;base64,{b64}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

# --- 🔊 4. ฟังก์ชันสร้างเสียงหวานพรีเมียม ---
async def make_voice(text):
    try:
        VOICE = "th-TH-PremwadeeNeural"
        communicate = edge_tts.Communicate(text, VOICE, rate="-15%", pitch="+3Hz")
        await communicate.save("rin_voice.mp3")
        return True
    except: return False

# --- 💾 5. ระบบจัดการ Session ---
if "messages" not in st.session_state: st.session_state.messages = []

# --- 🛠️ 6. Sidebar (การตั้งค่าที่บอสถามหา) ---
with st.sidebar:
    st.markdown("### 👓 Rin Settings")
    st.write("บอสตั้งค่ารินตรงนี้ได้เลยนะคะ")
    think_lvl = st.radio("ระดับการค้นหา:", ("ค้นหาปกติ (Standard)", "ค้นหาขั้นสูง (Max Search ✨)"))
    voice_on = st.toggle("เปิดเสียงเลขาริน", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

# --- 7. ส่วนแสดงผลหลัก ---
show_rin()
st.markdown("<h3 style='text-align: center;'>Rin Secretary v33.0</h3>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 🎤 ส่วนรับคำสั่ง (ไมค์ & พิมพ์) ---
col_mic, col_in = st.columns([1, 6])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#333333", recording_color="#ff4b4b")

prompt = st.chat_input("สั่งรินจดออเดอร์ หรือถามราคา LUNC ได้เลยค่ะบอส...")

final_input = None
if audio:
    with st.spinner("รินฟังอยู่ค่ะ..."):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "wb") as f: f.write(audio)
        with open("t.wav", "rb") as f:
            final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text
elif prompt:
    final_input = prompt

# --- 🤖 8. การประมวลผลคำสั่ง ---
if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        # กรณีสั่งให้จดบันทึก
        if any(w in final_input for w in ["จด", "บันทึก", "จำ"]):
            if save_to_rin_memory(final_input):
                answer = "เรียบร้อยค่ะบอส! รินจดเรื่องนี้ลง Google Sheets ให้แล้วนะคะ 👓✨💖"
            else:
                answer = "รินจดไม่ได้ค่ะบอส ลองเช็คสิทธิ์การแชร์ไฟล์ Sheets ดูนะ คะ"
        else:
            # กรณีแชทหรือค้นหา
            with st.spinner("รินกำลังคิดนะคะ..."):
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                
                context = ""
                # ค้นหาถ้าบอสเลือก Max Search หรือพิมพ์คำสำคัญ
                if "Max" in think_lvl or any(w in final_input for w in ["ราคา", "ข่าว", "เช็ค", "คืออะไร"]):
                    try:
                        res = tavily.search(query=final_input, max_results=3)
                        context = "\n".join([r['content'] for r in res['results']])
                    except: context = ""

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"คุณคือริน เลขาบ
