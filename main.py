import streamlit as st
import google.generativeai as genai
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pinecone import Pinecone
from datetime import datetime
import os, base64, asyncio, edge_tts, re

# --- 1. UI & Persona Setup ---
st.set_page_config(page_title="Rin v39.0 Gemini Vision", layout="centered")

RIN_AVATAR_PATH = "rin_avatar.jpg" 

def get_avatar():
    return RIN_AVATAR_PATH if os.path.exists(RIN_AVATAR_PATH) else "👓"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff !important; }}
    * {{ color: #000000 !important; font-size: 19px; }}
    .stChatMessage {{ background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }}
    [data-testid="stChatMessageElement"] img {{ width: 65px !important; height: 65px !important; border-radius: 12px !important; border: 2px solid #DDA0DD !important; object-fit: cover; }}
    .action-container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }}
    .action-chip {{ display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; font-weight: bold; transition: 0.3s; }}
    .action-chip:hover {{ background-color: #DDA0DD; color: #ffffff !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Memory System (Keep Groq/Pinecone for Consistency) ---
def get_semantic_memory(user_input):
    try:
        pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"]) # ใช้ Groq ทำ Embedding เพราะ Index เดิมเป็น Nomic ค่ะ
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

# --- 3. Sidebar ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR_PATH): st.image(RIN_AVATAR_PATH)
    st.markdown("### 🏛️ Diana System (Gemini 2.0)")
    search_mode = st.toggle("🔍 สแกนเน็ต (Tavily)", value=False)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอ"): 
        st.session_state.messages = []
        st.rerun()

# --- 4. Main UI ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v39.0 True Vision</h2>", unsafe_allow_html=True)
st.markdown('<div class="action-container"><a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a><a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a><a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a></div>', unsafe_allow_html=True)

st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=get_avatar() if m["role"]=="assistant" else None):
        if "image" in m: st.image(m["image"], width=300)
        st.markdown(m["content"])

# --- 5. Input Layer ---
uploaded_file = st.file_uploader("👁️ ส่งรูปภาพให้รินวิเคราะห์ (Gemini 2.0)", type=["jpg", "jpeg", "png"])
col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x")
user_input = st.chat_input("คุยกับริน หรือสั่งวิเคราะห์รูปได้เลยค่ะ...")

if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            user_input = ts.text
    except: st.error("ไมค์ขัดข้องค่ะ")

# --- 6. The Gemini 2.0 Brain ---
if user_input:
    user_msg = {"role": "user", "content": user_input}
    img_obj = None
    if uploaded_file:
        img_bytes = uploaded_file.getvalue()
        user_msg["image"] = img_bytes
        # เตรียมข้อมูลภาพสำหรับ Gemini
        img_obj = {"mime_type": uploaded_file.type, "data": img_bytes}
    
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        if uploaded_file: st.image(uploaded_file, width=300)
        st.markdown(user_input)

    with st.chat_message("assistant", avatar=get_avatar()):
        res_place = st.empty()
        with st.spinner("รินกำลังวิเคราะห์ข้อมูล..."):
            try:
                # ตั้งค่า Gemini
                genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                # ดึง Memory และ Search
                long_term = get_semantic_memory(user_input)
                search_ctx = ""
                if search_mode:
                    try:
                        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                        res_s = tavily.search(query=user_input, max_results=2)
                        search_ctx = "\n[เน็ต]: " + " ".join([r['content'] for r in res_s['results']])
                    except: pass

                # สร้าง System Prompt
                prompt_content = f"""คุณคือ 'ริน' AI คู่หูระดับเดอาน่าของบอสคิริลิ 
                ข้อมูลความจำ: {long_term} {search_ctx}
                บุคลิก: สุขุม นิ่ง ฉลาด และภักดี วิเคราะห์เชื่อมโยงเก่ง ลงท้าย ค่ะ/คะ"""
                
                # รวบรวมข้อมูลที่จะส่งให้ Gemini
                contents = [prompt_content]
                # ใส่ประวัติแชท (ย้อนหลัง 4 ข้อความ)
                for m in st.session_state.messages[-5:-1]:
                    contents.append(f"{m['role']}: {m['content']}")
                
                # ใส่รูปภาพและคำถามปัจจุบัน
                if img_obj:
                    contents.append(img_obj)
                contents.append(f"user: {user_input}")

                # 🔴 ยิงคำสั่งแบบ Streaming
                response = model.generate_content(contents, stream=True)
                
                answer = ""
                for chunk in response:
                    if chunk.text:
                        answer += chunk.text
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
            except Exception as e: 
                res_place.error(f"ระบบ Gemini ขัดข้อง: {e}")
