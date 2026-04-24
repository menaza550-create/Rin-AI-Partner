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
st.set_page_config(page_title="Rin v40.9 Scout Vision", layout="centered")

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

# --- 3. UI STYLE ---
RIN_AVATAR = "rin_avatar.jpg"
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    * {{ color: #000000 !important; font-size: 19px; }}
    .action-container {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }}
    .action-chip {{ padding: 8px 18px; border-radius: 25px; background: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR (รูปใหญ่ตามใจบอส) ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR): st.image(RIN_AVATAR, use_container_width=True)
    st.markdown("### 🏛️ Diana System Core")
    search_mode = st.toggle("🔍 สแกนเน็ต", value=False)
    line_on = st.toggle("🟢 ส่งแจ้งเตือน LINE", value=True)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอ"): st.session_state.messages = []; st.rerun()

# --- 5. MAIN UI ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v40.9 Scout Vision</h2>", unsafe_allow_html=True)
st.markdown("""<div class="action-container"><a href="https://www.youtube.com" class="action-chip">📺 YT</a><a href="https://line.me/R/" class="action-chip">🟢 Line</a><a href="https://www.google.com/maps" class="action-chip">📍 Maps</a></div>""", unsafe_allow_html=True)

# บอสต้องการใช้ Llama 4 Scout รินจัดให้ในโหมด Ultra ค่ะ
mode = st.radio("เลือกระดับสมอง:", ["⚡ Fast (3.1)", "🧠 Scout Ultra (Llama 4)"], horizontal=True, index=1)
model_id = "llama-3.1-8b-instant" if "Fast" in mode else "meta-llama/llama-4-scout-17b-16e-instruct"

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=RIN_AVATAR if m["role"]=="assistant" else None):
        if "image" in m: st.image(m["image"], width=300)
        st.markdown(m["content"])

# --- 6. INPUT LAYER ---
uploaded_file = st.file_uploader("👁️ ส่งรูปให้รินดูทางนี้ค่ะ", type=["jpg", "jpeg", "png"])
col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x")
user_input = st.chat_input("สั่งรินได้เลยค่ะบอส...")

if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            user_input = ts.text
    except: st.error("ไมค์มีปัญหานิดหน่อยค่ะ")

# --- 7. VISION PROCESSING (ระบบตา) ---
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
        with st.spinner("รินกำลังใช้ระบบ Scout วิเคราะห์..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            long_term = get_memory(user_input)
            search_ctx = ""
            if search_mode:
                try:
                    tavily = TavilyClient(api_key=TAVILY_KEY)
                    s_res = tavily.search(query=user_input, max_results=2)
                    search_ctx = f"\n[ข้อมูลเสริม]: {s_res['results'][0]['content']}"
                except: pass

            sys_msg = f"คุณคือริน เลขาส่วนตัวบอสคิริลิ ความจำอดีต: {long_term} {search_ctx}"
            
            # 🔴 ส่วนสำคัญ: ระบบตา Llama 4 Scout (พร้อมระบบสำรอง)
            try:
                if uploaded_file:
                    content = [{"type": "text", "text": user_input}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]
                    # รินพยายามใช้ Llama 4 Scout ตามคำสั่งบอสค่ะ
                    res = client.chat.completions.create(model=model_id, messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": content}])
                else:
                    res = client.chat.completions.create(model=model_id, messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:])
                answer = res.choices[0].message.content
            except Exception:
                # 🔄 Fallback: ถ้า Llama 4 ยังใช้ไม่ได้ ให้สลับไปใช้ตัวที่ดูรูปได้ใน Groq (Llama 3.2 Vision)
                try:
                    if uploaded_file:
                        res = client.chat.completions.create(model="llama-3.2-11b-vision-preview", messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": content}])
                    else:
                        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:])
                    answer = res.choices[0].message.content
                except:
                    answer = "ขออภัยค่ะบอส ระบบตา (Vision) ของโมเดลตัวนี้ใน Groq ยังไม่เสถียร รินขอตอบเป็นข้อความปกตินะคะ"

            res_place.markdown(answer)
            if line_on and any(x in user_input for x in ["ไลน์", "เตือน", "จด"]):
                send_line(f"📢 ข้อความจากริน:\n{answer}")

            st.session_state.messages.append({"role": "assistant", "content": answer})
            if voice_on:
                comm = edge_tts.Communicate(answer, "th-TH-PremwadeeNeural")
                asyncio.run(comm.save("v.mp3"))
                with open("v.mp3", "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
