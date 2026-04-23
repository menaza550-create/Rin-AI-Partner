import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pinecone import Pinecone
from datetime import datetime
import os, base64, asyncio, edge_tts, re

# --- 1. UI & Persona Setup ---
st.set_page_config(page_title="Rin v38.17 Lightning", layout="centered")

RIN_AVATAR_PATH = "rin_avatar.jpg" 

def get_avatar():
    return RIN_AVATAR_PATH if os.path.exists(RIN_AVATAR_PATH) else "👓"

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

# --- 2. Memory System (Pinecone) ---
def get_semantic_memory(user_input):
    try:
        pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=user_input)
        search_results = index.query(vector=res.data[0].embedding, top_k=2, include_metadata=True)
        return "\n".join([f"{match['metadata']['text']}" for match in search_results['matches']]) if search_results['matches'] else ""
    except: return ""

def save_semantic_memory(u_input, r_output):
    try:
        pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=u_input)
        index.upsert(vectors=[{"id": datetime.now().strftime("%Y%m%d%H%M%S"), "values": res.data[0].embedding, "metadata": {"text": u_input, "reply": r_output}}])
    except: pass

# --- 3. Sidebar (Debug & Tools) ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR_PATH): st.image(RIN_AVATAR_PATH)
    st.markdown("### 🏛️ Diana System Core")
    
    if st.button("🔍 ตรวจสอบสมองที่ใช้ได้"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            for m in client.models.list().data: st.code(m.id)
        except Exception as e: st.error(f"Error: {e}")
        
    search_mode = st.toggle("🔍 สแกนเน็ต", value=False)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอ"): 
        st.session_state.messages = []
        st.rerun()

# --- 4. Main UI ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v38.17 Lightning</h2>", unsafe_allow_html=True)
st.markdown('<div class="action-container"><a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a><a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a><a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a></div>', unsafe_allow_html=True)

ai_mode = st.radio("เลือกระดับสมอง:", ["⚡ Fast (3.1)", "🧠 Ultra (Llama 4)"], index=1)
model_mapping = {
    "⚡ Fast (3.1)": "llama-3.1-8b-instant", 
    "🧠 Ultra (Llama 4)": "meta-llama/llama-4-scout-17b-16e-instruct"
}
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=get_avatar() if m["role"]=="assistant" else None):
        if "image" in m: st.image(m["image"], width=300)
        st.markdown(m["content"])

# --- 5. Input Layer ---
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

# --- 6. Brain Processing (The Llama 4 Engine) ---
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

    with st.chat_message("assistant", avatar=get_avatar()):
        res_place = st.empty()
        with st.spinner("รินกำลังวิเคราะห์..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                long_term = get_semantic_memory(user_input)
                
                # 🔍 กู้ระบบสแกนเน็ตคืนมาค่ะ!
                search_ctx = ""
                if search_mode:
                    try:
                        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                        res_search = tavily.search(query=user_input, max_results=2)
                        search_ctx = "\n[ข้อมูลสดจากเน็ต]: " + " ".join([r['content'] for r in res_search['results']])
                    except: pass

                sys_msg = f"คุณคือ 'ริน' AI คู่หูบอสคิริลิ ความจำ: {long_term} {search_ctx} ตอบสุขุม ฉลาด ภักดี ค่ะ/คะ"
                
                history = [{"role": "system", "content": sys_msg}]
                for m in st.session_state.messages[-4:-1]:
                    history.append({"role": m["role"], "content": m["content"]})

                # 🔴 การจัดการรูปภาพแบบ Fallback
                active_model = model_mapping[ai_mode]
                stream_res = None

                if uploaded_file:
                    try:
                        v_content = [
                            {"type": "text", "text": user_input + " (วิเคราะห์รูปนี้ด้วยค่ะ)"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]
                        stream_res = client.chat.completions.create(model=active_model, messages=history + [{"role": "user", "content": v_content}], stream=True)
                    except Exception:
                        res_place.warning("บอสคะ ไอดี Groq นี้ยังดูรูปไม่ได้ รินขอตอบเป็นข้อความแทนนะคะ")
                        stream_res = client.chat.completions.create(model=active_model, messages=history + [{"role": "user", "content": user_input}], stream=True)
                else:
                    stream_res = client.chat.completions.create(model=active_model, messages=history + [{"role": "user", "content": user_input}], stream=True)

                answer = ""
                for chunk in stream_res:
                    if chunk.choices[0].delta.content:
                        answer += chunk.choices[0].delta.content
                        res_place.markdown(answer + "▌")
                
                res_place.markdown(answer)
                save_semantic_memory(user_input, answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

                if voice_on:
                    comm = edge_tts.Communicate(answer, "th-TH-PremwadeeNeural", rate="-10%", pitch="+2Hz")
                    asyncio.run(comm.save("v.mp3"))
                    with open("v.mp3", "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                        st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
            except Exception as e: res_place.error(f"ระบบขัดข้อง: {e}")
