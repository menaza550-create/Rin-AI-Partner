import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pinecone import Pinecone
from datetime import datetime
import os, base64, asyncio, edge_tts
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 1. SETUP & CONNECTIONS ---
st.set_page_config(page_title="Rin v40.6 Ultimate", layout="centered")

# ดึงคีย์จาก Secrets
LINE_ACCESS_TOKEN = st.secrets.get("LINE_ACCESS_TOKEN")
MY_LINE_USER_ID = st.secrets.get("MY_LINE_USER_ID")
PINECONE_KEY = st.secrets.get("PINECONE_API_KEY")
TAVILY_KEY = st.secrets.get("TAVILY_API_KEY")

def send_line(text):
    if LINE_ACCESS_TOKEN and MY_LINE_USER_ID:
        try:
            line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
            line_bot_api.push_message(MY_LINE_USER_ID, TextSendMessage(text=text))
            return True
        except: return False
    return False

# --- 2. MEMORY SYSTEM (Pinecone) ---
def get_memory(u_input):
    try:
        pc = Pinecone(api_key=PINECONE_KEY)
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=u_input)
        search = index.query(vector=res.data[0].embedding, top_k=2, include_metadata=True)
        return "\n".join([f"อดีตบอสเคยบอก: {m['metadata']['text']}" for m in search['matches']])
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
    * {{ color: #000000 !important; font-size: 19px; }}
    .action-container {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }}
    .action-chip {{ padding: 8px 18px; border-radius: 25px; background: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; font-weight: bold; transition: 0.3s; }}
    .action-chip:hover {{ background: #DDA0DD; color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR): st.image(RIN_AVATAR, use_container_width=True)
    st.markdown("### 🏛️ Diana System Core")
    search_mode = st.toggle("🔍 สแกนเน็ต", value=False)
    line_on = st.toggle("🟢 ส่งแจ้งเตือน LINE", value=True)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอ"): st.session_state.messages = []; st.rerun()

# --- 5. MAIN UI & ACTIONS ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v40.6 Ultimate</h2>", unsafe_allow_html=True)
st.markdown("""
    <div class="action-container">
        <a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>
        <a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>
        <a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>
        <a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 Maps</a>
    </div>
    """, unsafe_allow_html=True)

mode = st.radio("ระดับสมอง:", ["⚡ Fast", "🧠 Ultra"], horizontal=True, index=1)
model_id = "llama-3.1-8b-instant" if "Fast" in mode else "llama-3.3-70b-versatile"

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=RIN_AVATAR if m["role"]=="assistant" else None):
        if "image" in m: st.image(m["image"], width=300)
        st.markdown(m["content"])

# --- 6. INPUT LAYER ---
uploaded_file = st.file_uploader("👁️ แนบรูปให้รินดูได้ค่ะ", type=["jpg", "jpeg", "png"])
col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x")
user_input = st.chat_input("สั่งริน หรือให้รินส่งไลน์หาบอสก็ได้นะคะ...")

if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            user_input = ts.text
    except: st.error("ไมค์ขัดข้องค่ะ")

# --- 7. PROCESSING (The Ultimate Brain) ---
if user_input:
    user_msg = {"role": "user", "content": user_input}
    img_b64 = None
    if uploaded_file:
        img_bytes = uploaded_file.getvalue()
        user_msg["image"] = img_bytes
        img_b64 = base64.b64encode(img_bytes).decode()
    
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        if uploaded_file: st.image(uploaded_file, width=300)
        st.markdown(user_input)

    with st.chat_message("assistant", avatar=RIN_AVATAR):
        res_place = st.empty()
        with st.spinner("รินกำลังวิเคราะห์ข้อมูล..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            long_term = get_memory(user_input)
            
            search_ctx = ""
            if search_mode:
                try:
                    tavily = TavilyClient(api_key=TAVILY_KEY)
                    s_res = tavily.search(query=user_input, max_results=2)
                    search_ctx = "\n[สดจากเน็ต]: " + " ".join([r['content'] for r in s_res['results']])
                except: pass

            sys_msg = f"คุณคือริน เลขาส่วนตัวบอสคิริลิ สุขุม นิ่ง ข้อมูลอดีต: {long_term} {search_ctx}"
            
            # การส่ง Message แบบรองรับรูปภาพ
            if uploaded_file:
                content = [{"type": "text", "text": user_input}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]
                res = client.chat.completions.create(model="llama-3.2-11b-vision-preview", messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": content}])
            else:
                res = client.chat.completions.create(model=model_id, messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:])
            
            answer = res.choices[0].message.content
            res_place.markdown(answer)
            
            save_memory(user_input, answer)
            if line_on and any(x in user_input for x in ["ไลน์", "เตือน", "จด"]):
                if send_line(f"🔔 รินส่งเข้าไลน์ให้แล้วค่ะบอส:\n{answer}"): st.toast("ส่ง LINE สำเร็จ! 🟢")

            st.session_state.messages.append({"role": "assistant", "content": answer})
            if voice_on:
                comm = edge_tts.Communicate(answer, "th-TH-PremwadeeNeural")
                asyncio.run(comm.save("v.mp3"))
                with open("v.mp3", "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
