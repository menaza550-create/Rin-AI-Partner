import streamlit as st
from groq import Groq
from pinecone import Pinecone
from datetime import datetime
import os, base64, asyncio, edge_tts
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 1. SETUP & LINE ---
st.set_page_config(page_title="Rin v40.2 Complete", layout="wide")

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

# --- 2. MEMORY SYSTEM (768 Dimensions) ---
def get_memory(u_input):
    try:
        pc = Pinecone(api_key=PINECONE_KEY)
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=u_input)
        search = index.query(vector=res.data[0].embedding, top_k=2, include_metadata=True)
        return "\n".join([m['metadata']['text'] for m in search['matches']])
    except: return ""

def save_memory(u_input, r_output):
    try:
        pc = Pinecone(api_key=PINECONE_KEY)
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=u_input)
        index.upsert(vectors=[{"id": datetime.now().strftime("%Y%m%d%H%M%S"), "values": res.data[0].embedding, "metadata": {"text": u_input, "reply": r_output}}])
    except: pass

# --- 3. UI STYLE ---
RIN_AVATAR = "rin_avatar.jpg"
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    * {{ color: #000000 !important; font-size: 18px; }}
    .action-container {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 25px; }}
    .action-chip {{ padding: 8px 18px; border-radius: 20px; background: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR & MAIN ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR): st.image(RIN_AVATAR, use_container_width=True)
    st.markdown("### 🏛️ Diana Core")
    line_on = st.toggle("🟢 ส่งแจ้งเตือน LINE", value=True)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างแชท"): st.session_state.messages = []; st.rerun()

st.markdown("<h2 style='text-align:center;'>👓 Rin v40.2 Complete System</h2>", unsafe_allow_html=True)

# 🔙 เอากลับมาแล้วค่ะบอส! ปุ่มทางลัดที่หายไป
st.markdown("""
    <div class="action-container">
        <a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>
        <a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>
        <a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>
        <a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 Maps</a>
    </div>
    """, unsafe_allow_html=True)

mode = st.radio("ระดับสมอง:", ["⚡ Fast (8B)", "🧠 Ultra (70B)"], horizontal=True)
model_id = "llama-3.1-8b-instant" if "Fast" in mode else "llama-3.3-70b-versatile"

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=RIN_AVATAR if m["role"]=="assistant" else None): st.markdown(m["content"])

# --- 5. PROCESS ---
user_input = st.chat_input("สั่งรินได้เลยค่ะบอส...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant", avatar=RIN_AVATAR):
        placeholder = st.empty()
        with st.spinner("รินกำลังประมวลผล..."):
            past_mem = get_memory(user_input)
            sys_msg = f"คุณคือริน เลขาสมบูรณ์แบบ สุขุม นิ่ง ข้อมูลอดีต: {past_mem}"
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            res = client.chat.completions.create(model=model_id, messages=[{"role":"system","content":sys_msg}]+st.session_state.messages[-5:])
            ans = res.choices[0].message.content
            placeholder.markdown(ans)
            
            save_memory(user_input, ans)
            if line_on and any(x in user_input for x in ["ไลน์", "เตือน", "จด"]):
                if send_line(f"🔔 รินจดให้แล้วค่ะบอส:\n{ans}"): st.toast("ส่ง LINE สำเร็จ! 🟢")

            st.session_state.messages.append({"role": "assistant", "content": ans})
            if voice_on:
                comm = edge_tts.Communicate(ans, "th-TH-PremwadeeNeural")
                asyncio.run(comm.save("r.mp3"))
                with open("r.mp3", "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
