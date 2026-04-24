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
st.set_page_config(page_title="Rin v40.22 90B Vision Upgrade", layout="centered")

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

# --- 2. UI STYLE ---
RIN_AVATAR = "rin_avatar.jpg"
def get_avatar():
    return RIN_AVATAR if os.path.exists(RIN_AVATAR) else "👓"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff !important; }}
    * {{ color: #000000 !important; font-size: 19px; }}
    .stChatMessage {{ background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }}
    [data-testid="stChatMessageElement"] img {{ width: 65px !important; height: 65px !important; border-radius: 12px !important; border: 2px solid #DDA0DD !important; object-fit: cover; }}
    [data-testid="stChatMessageContent"] {{ margin-left: 15px !important; }}
    .action-container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }}
    .action-chip {{ display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; font-size: 16px !important; font-weight: bold; transition: 0.3s; text-align: center; }}
    .action-chip:hover {{ background-color: #DDA0DD; color: #ffffff !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
    div[data-testid="stRadio"] > div {{ flex-direction: row; align-items: center; justify-content: center; background-color: #f8f9fa; padding: 10px; border-radius: 15px; border: 1px solid #eee; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR): st.image(RIN_AVATAR, use_container_width=True)
    st.markdown("### 🏛️ Diana System Core")
    
    # 🟢 เพิ่มปุ่มเลือกโมเดลตา ให้บอสเทสได้ตามใจชอบเลยค่ะ!
    st.markdown("**👁️ ระบบตา (ดูรูปภาพ):**")
    vision_model = st.radio("เลือกตา:", ["llama-3.2-90b-vision-preview", "meta-llama/llama-4-scout-17b-16e-instruct"], label_visibility="collapsed")
    st.write("---")
    
    if st.button("🔍 ตรวจสอบสมองที่ใช้ได้"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            for m in client.models.list().data: st.code(m.id)
        except Exception as e: st.error(f"Error: {e}")

    search_mode = st.toggle("🔍 สแกนเน็ต", value=False)
    line_on = st.toggle("🟢 ส่งแจ้งเตือน LINE", value=True)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอ"): st.session_state.messages = []; st.rerun()

# --- 4. MAIN UI ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v40.22 90B Vision Upgrade</h2>", unsafe_allow_html=True)

st.markdown("""
    <div class="action-container">
        <a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 Maps</a>
        <a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>
        <a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>
        <a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>
    </div>
    """, unsafe_allow_html=True)

mode = st.radio("🧠 ระบบสมอง (คุยข้อความ):", ["⚡ Fast (8B)", "🧠 Ultra (70B)"], horizontal=True)
text_model_id = "llama-3.1-8b-instant" if "Fast" in mode else "llama-3.3-70b-versatile"

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=get_avatar() if m["role"]=="assistant" else None):
        if "image" in m: st.image(m["image"], width=300)
        st.markdown(m["content"])

# --- 5. INPUT LAYER ---
uploaded_file = st.file_uploader("👁️ แนบรูปภาพให้รินดู", type=["jpg", "jpeg", "png"])
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
    except: st.error("ไมค์ขัดข้องค่ะ")

# --- 6. VISION & PROCESSING ---
if user_input:
    user_msg = {"role": "user", "content": user_input}
    img_b64 = None
    mime_type = "image/jpeg"
    
    if uploaded_file:
        img_bytes = uploaded_file.getvalue()
        user_msg["image"] = img_bytes
        img_b64 = base64.b64encode(img_bytes).decode()
        mime_type = uploaded_file.type 
    
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        if uploaded_file: st.image(uploaded_file, width=300)
        st.markdown(user_input)

    with st.chat_message("assistant", avatar=get_avatar()):
        res_place = st.empty()
        with st.spinner(f"รินกำลังวิเคราะห์รูปด้วยตา {vision_model}..." if uploaded_file else "รินกำลังคิด..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            long_term = get_memory(user_input)
            search_ctx = ""
            if search_mode:
                try:
                    tavily = TavilyClient(api_key=TAVILY_KEY)
                    s_res = tavily.search(query=user_input, max_results=2)
                    search_ctx = "\n[สดจากเน็ต]: " + " ".join([r['content'] for r in s_res['results']])
                except: pass

            sys_msg = f"คุณคือริน เลขาส่วนตัวบอสคิริลิ ความจำอดีต: {long_term} {search_ctx}"
            
            history = [{"role": "system", "content": sys_msg}]
            for m in st.session_state.messages[-4:-1]:
                history.append({"role": m["role"], "content": m["content"]})

            answer = ""
            try:
                if uploaded_file:
                    # 👁️ สวมแว่นตาตัวที่บอสเลือกจาก Sidebar (เช่น 90b-vision)
                    v_content = [
                        {"type": "text", "text": user_input}, 
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{img_b64}"}}
                    ]
                    stream_res = client.chat.completions.create(
                        model=vision_model, 
                        messages=history + [{"role": "user", "content": v_content}],
                        stream=True
                    )
                else:
                    # 🧠 ใช้สมองตัวที่บอสเลือกคุยข้อความปกติ
                    stream_res = client.chat.completions.create(
                        model=text_model_id, 
                        messages=history + [{"role": "user", "content": user_input}],
                        stream=True
                    )
                
                for chunk in stream_res:
                    if chunk.choices[0].delta.content:
                        answer += chunk.choices[0].delta.content
                        res_place.markdown(answer + "▌")
                        
                res_place.markdown(answer)
                
            except Exception as e:
                answer = f"ขออภัยค่ะบอส ระบบประมวลผลมีปัญหาแจ้งว่า: {str(e)}"
                res_place.error(answer)

            save_memory(user_input, answer)
            
            if line_on and any(x in user_input for x in ["ไลน์", "เตือน", "จด"]):
                send_line(f"📢 ข้อความจากริน:\n{answer}")

            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            if voice_on:
                comm = edge_tts.Communicate(answer, "th-TH-PremwadeeNeural", rate="-10%", pitch="+2Hz")
                asyncio.run(comm.save("v.mp3"))
                with open("v.mp3", "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
