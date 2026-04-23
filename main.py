import streamlit as st
from groq import Groq
from pinecone import Pinecone
from datetime import datetime
import os, base64, asyncio, edge_tts
from linebot import LineBotApi
from linebot.models import TextSendMessage
from audio_recorder_streamlit import audio_recorder

# --- 1. SETUP & CONNECTIONS ---
st.set_page_config(page_title="Rin v40.5 Full Power", layout="centered")

LINE_ACCESS_TOKEN = st.secrets.get("LINE_ACCESS_TOKEN")
MY_LINE_USER_ID = st.secrets.get("MY_LINE_USER_ID")
PINECONE_KEY = st.secrets.get("PINECONE_API_KEY")

def send_line(text):
    if LINE_ACCESS_TOKEN and MY_LINE_USER_ID:
        try:
            line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
            line_bot_api.push_message(MY_LINE_USER_ID, TextSendMessage(text=text))
            return True
        except: return False
    return False

# --- 2. SEMANTIC MEMORY (ดึงข้อมูลจาก Database) ---
def get_memory(u_input):
    try:
        pc = Pinecone(api_key=PINECONE_KEY)
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        # แปลงคำถามเป็น Vector เพื่อไปค้นใน Database
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=u_input)
        search = index.query(vector=res.data[0].embedding, top_k=3, include_metadata=True)
        memories = [f"อดีตบอสเคยบอก: {m['metadata']['text']}" for m in search['matches']]
        return "\n".join(memories)
    except: return ""

def save_memory(u_input, r_output):
    try:
        pc = Pinecone(api_key=PINECONE_KEY)
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=u_input)
        index.upsert(vectors=[{"id": datetime.now().strftime("%Y%m%d%H%M%S"), 
                               "values": res.data[0].embedding, 
                               "metadata": {"text": u_input, "reply": r_output}}])
    except: pass

# --- 3. UI STYLE ---
RIN_AVATAR = "rin_avatar.jpg"
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    * {{ color: #000000 !important; font-size: 18px; }}
    .action-container {{ display: flex; justify-content: center; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }}
    .action-chip {{ padding: 6px 12px; border-radius: 20px; background: #f8f9fa; border: 1px solid #DDA0DD; text-decoration: none; font-weight: bold; font-size: 13px !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR (คงรูปรินขนาดใหญ่ไว้ตามใจบอส) ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR): 
        st.image(RIN_AVATAR, use_container_width=True) # รูปรินใหญ่แบบที่บอสชอบ
    st.markdown("### 🏛️ Diana System Core")
    line_on = st.toggle("🟢 ส่งแจ้งเตือน LINE", value=True)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอแชท"): st.session_state.messages = []; st.rerun()

# --- 5. MAIN UI ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v40.5 Full Power</h2>", unsafe_allow_html=True)

# ปุ่มทางลัด
st.markdown("""
    <div class="action-container">
        <a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>
        <a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>
        <a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>
        <a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 Maps</a>
    </div>
    """, unsafe_allow_html=True)

mode = st.radio("ระดับสมอง:", ["⚡ Fast", "🧠 Ultra"], horizontal=True)
model_id = "llama-3.1-8b-instant" if "Fast" in mode else "llama-3.3-70b-versatile"

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=RIN_AVATAR if m["role"]=="assistant" else None): 
        st.markdown(m["content"])

# --- 6. INPUT LAYER (ไมค์กลับมาแล้วค่ะ!) ---
col_mic, col_input = st.columns([1, 6])
with col_mic: 
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")

user_input = st.chat_input("สั่งริน หรือพูดผ่านไมค์ได้เลยค่ะบอส...")

if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            user_input = ts.text
    except: st.error("ระบบรับเสียงขัดข้อง")

# --- 7. PROCESSING (เชื่อมต่อ Database) ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant", avatar=RIN_AVATAR):
        placeholder = st.empty()
        with st.spinner("รินกำลังค้นหาความจำและประมวลผล..."):
            # 🔍 ดึงข้อมูลจาก Database (Pinecone)
            past_mem = get_memory(user_input)
            
            sys_msg = f"คุณคือริน เลขาส่วนตัวของบอสคิริลิ สุขุม นิ่ง ข้อมูลจากความจำบอส: {past_mem}"
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            res = client.chat.completions.create(model=model_id, messages=[{"role":"system","content":sys_msg}]+st.session_state.messages[-5:])
            ans = res.choices[0].message.content
            placeholder.markdown(ans)
            
            # บันทึกความจำใหม่ลง Database
            save_memory(user_input, ans)
            
            # ส่ง LINE
            if line_on and any(x in user_input for x in ["ไลน์", "เตือน", "จด"]):
                if send_line(f"🔔 รินจดให้แล้วค่ะบอส:\n{ans}"): st.toast("ส่ง LINE สำเร็จ! 🟢")

            st.session_state.messages.append({"role": "assistant", "content": ans})
            if voice_on:
                comm = edge_tts.Communicate(ans, "th-TH-PremwadeeNeural")
                asyncio.run(comm.save("r.mp3"))
                with open("r.mp3", "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
