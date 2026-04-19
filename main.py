import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pyairtable import Api
from datetime import datetime
import os, base64, asyncio, edge_tts, pandas as pd

# --- 1. การตั้งค่าหน้าตาแอป (UI & Styling) ---
st.set_page_config(page_title="Rin v34.9.4 Partner", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 20px; }
    .stChatMessage { background-color: #f8f9fa !important; border: 1px solid #e0e0e0 !important; border-radius: 12px; }
    .crypto-card { background-color: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid #DDA0DD; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ระบบจัดการ Airtable (จด + อ่าน) ---
def get_airtable_table():
    try:
        api = Api(st.secrets["AIRTABLE_TOKEN"])
        return api.table(st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])
    except: return None

def save_to_memory(user_input, rin_output):
    try:
        table = get_airtable_table()
        if not table: return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        table.create({"Date": now, "User": user_input, "Rin": rin_output})
        return True
    except: return False

def read_last_memory(limit=5):
    try:
        table = get_airtable_table()
        if not table: return "ระบบจำไม่ได้เชื่อมต่อค่ะ"
        records = table.all(max_records=limit, sort=["-Date"])
        if not records: return "ยังไม่มีประวัติการจดค่ะ"
        return "\n".join([f"- {r['fields'].get('User')}" for r in records])
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

# --- 4. Sidebar ---
with st.sidebar:
    st.markdown("### Rin Settings 👓")
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

show_rin()
st.markdown("<h3 style='text-align:center;'>Rin v34.9.4 Partner</h3>", unsafe_allow_html=True)

# แสดงแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. ส่วนรับคำสั่ง (แก้ปัญหาลำดับความสำคัญ) ---
col_mic, col_input = st.columns([1, 5])
with col_mic:
    # เพิ่ม key เพื่อให้ไมค์รีเซ็ตสถานะได้ดีขึ้น
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444", key="rin_mic_v4")

prompt = st.chat_input("คุยกับริน หรือสั่งให้ริน 'จด' ได้เลยค่ะ...")
final_input = None

# ✅ จุดสำคัญ: ให้ "พิมพ์" (Prompt) มาก่อน "เสียง" (Audio) เสมอ
if prompt:
    final_input = prompt
elif audio:
    with st.spinner("รินกำลังฟัง..."):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            with open("temp.wav", "wb") as f: f.write(audio)
            with open("temp.wav", "rb") as f:
                trans = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
                text = trans.text
                # กรองคำหูแว่ว (Dealing / Thank you)
                if text.strip().lower() not in ["dealing.", "dealing", "thank you.", "thank you"] and len(text) > 2:
                    final_input = text
        except: pass

# --- 6. ประมวลผลและตอบกลับ ---
if final_input:
    # ป้องกันการส่งซ้ำ
    if not st.session_state.messages or final_input != st.session_state.messages[-1]["content"]:
        st.session_state.messages.append({"role": "user", "content": final_input})
        with st.chat_message("user"): st.markdown(final_input)

        with st.chat_message("assistant", avatar="👓"):
            past_mem = read_last_memory(5)
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                chat = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": f"คุณคือริน เลขาบอสคิริลิ พัทยา ความจำ: {past_mem}"}] + st.session_state.messages[-5:]
                )
                answer = chat.choices[0].message.content
                
                # ระบบจดบันทึก
                if any(w in final_input for w in ["จด", "บันทึก"]):
                    if save_to_memory(final_input, answer):
                        answer += "\n\n(รินจดลง Airtable ให้แล้วค่ะ 📝)"

                st.markdown(answer)
                if voice_on:
                    asyncio.run(make_voice(answer))
                    st.audio("rin_voice.mp3", autoplay=True)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"สมองรินสะดุดค่ะ: {e}")
