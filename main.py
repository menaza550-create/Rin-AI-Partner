import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pyairtable import Api
from datetime import datetime
import os, base64, asyncio, edge_tts, pandas as pd

# --- 1. [OPTIMIZED] การตั้งค่าหน้าตาแอป ---
st.set_page_config(page_title="Rin v34.8 Partner", layout="centered", initial_sidebar_state="expanded")

# --- [NEW] ฟังก์ชันสำหรับจำไฟล์วิดีโอ (จำครั้งเดียว ไม่ต้องโหลดใหม่ทุกรอบ) ---
@st.cache_data
def get_video_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# --- [NEW] ฟังก์ชันจำราคาเหรียญ (จำไว้ 10 นาทีค่อยไปเช็กใหม่) ---
@st.cache_data(ttl=600) 
def fetch_crypto_status(api_key):
    try:
        tavily = TavilyClient(api_key=api_key)
        p_res = tavily.search(query="LUNC price USD today", max_results=1)
        return p_res["results"][0]["content"][:100]
    except:
        return "⚠️ โหลดราคาไม่ได้ค่ะ"

# CSS คงเดิม
st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 20px; }
    .action-chip { 
        display: inline-block; padding: 10px 20px; border-radius: 25px; 
        background-color: #f0f2f6; border: 2px solid #DDA0DD; 
        text-decoration: none; color: #000000 !important; font-weight: bold; 
    }
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
        if table:
            table.create({"Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "User": user_input, "Rin": rin_output})
            return True
    except: return False

@st.cache_data(ttl=60) # จำความจำล่าสุดไว้ 1 นาที (ไม่ต้องดึงใหม่ทุกครั้งที่พิมพ์)
def read_last_memory(limit=5):
    try:
        table = get_airtable_table()
        if not table: return ""
        records = table.all(max_records=limit, sort=["-Date"])
        return "\n".join([f"- {r['fields'].get('User')}" for r in records])
    except: return ""

# --- 3. [OPTIMIZED] ฟังก์ชันร่างริน ---
def show_rin():
    video_b64 = get_video_base64("1000024544.mp4")
    if video_b64:
        st.markdown(f'''<div style="display:flex;justify-content:center;margin-bottom:15px;"><video width="250" autoplay loop muted playsinline style="border-radius:15px;border:2px solid #DDA0DD;"><source src="data:video/mp4;base64,{video_b64}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. Sidebar: Dashboard (Turbo Mode) ---
with st.sidebar:
    st.markdown("### 📊 Business Dashboard")
    # ใช้ Cache ดึงข้อมูล จะทำให้ Sidebar ไม่ค้างเวลาคลิก
    status = fetch_crypto_status(st.secrets["TAVILY_API_KEY"])
    st.markdown(f'<div class="crypto-card"><b>LUNC Status:</b><br>{status}...</div>', unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### Rin Settings 👓")
    think_lvl = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.cache_data.clear() # ล้างความจำ Cache ด้วย
        st.rerun()

show_rin()
st.markdown("<h3 style='text-align:center;'>Rin v34.8 Partner</h3>", unsafe_allow_html=True)

# --- ACTION CHIPS ---
st.markdown('<div class="action-container" style="text-align:center; margin-bottom:20px;">'
    '<a href="https://maps.google.com" target="_blank" class="action-chip">📍 นำทาง</a> '
    '<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a> '
    '<a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a> '
    '<a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>'
    '</div>', unsafe_allow_html=True)

st.write("---")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. ส่วนรับคำสั่ง ---
col_mic, col_label = st.columns([1, 5])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")

prompt = st.chat_input("คุยกับริน หรือสั่งให้ริน 'จด' ได้เลยค่ะ...")
final_input = prompt

if audio:
    with st.spinner("รินฟังอยู่นะคะ..."):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            with open("t.wav", "wb") as f: f.write(audio)
            with open("t.wav", "rb") as f:
                transcription = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3")
                final_input = transcription.text
        except: pass

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        past_memory = read_last_memory(5)
        
        # ค้นหาข้อมูลถ้าจำเป็น
        context = ""
        if "Max" in think_lvl or any(w in final_input for w in ["ราคา", "ข่าว"]):
            try:
                search = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"]).search(query=final_input, max_results=2)
                context = "".join([r['content'] for r in search['results']])
            except: pass
            
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": f"คุณคือริน เลขาบอสคิริลิ ความจำ: {past_memory} ข้อมูลเน็ต: {context}"}] + st.session_state.messages[-5:]
        )
        answer = chat.choices[0].message.content
        
        if any(w in final_input for w in ["จด", "บันทึก"]):
            if save_to_memory(final_input, answer):
                answer += "\n\n(รินจดลง Airtable แล้วค่ะ 📝)"
                st.cache_data.clear() # บังคับให้อ่านค่าใหม่ครั้งหน้าเพราะข้อมูลเปลี่ยนแล้ว
        
        st.markdown(answer)
        if voice_on:
            asyncio.run(make_voice(answer))
            st.audio("rin_voice.mp3", autoplay=True)
        st.session_state.messages.append({"role": "assistant", "content": answer})
