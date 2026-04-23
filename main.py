import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pinecone import Pinecone
from datetime import datetime
import os, base64, asyncio, edge_tts, re

# --- 1. UI & Persona Setup ---
st.set_page_config(page_title="Rin v38.15 The Seer", layout="centered")

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

# --- 2. Semantic Vector Memory (Pinecone) ---
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

# --- 3. Sidebar (เพิ่มระบบตรวจสอบสมอง) ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR_PATH): st.image(RIN_AVATAR_PATH)
    st.markdown("### 🏛️ Diana System Core")
    
    # 🔴 ปุ่มลับ: สแกนหาชื่อโมเดลที่ใช้ได้จริง
    if st.button("🔍 สแกนหาชื่อสมองที่ใช้ได้ (Debug)"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            models = client.models.list()
            st.write("รายชื่อสมองที่บอสใช้ได้ตอนนี้:")
            for m in models.data:
                st.code(m.id)
        except Exception as e: st.error(f"สแกนไม่ได้: {e}")
        
    search_mode = st.toggle("🔍 โหมดสแกนเน็ต", value=False)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอแชท"): 
        st.session_state.messages = []
        st.rerun()

# --- 4. Main UI ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v38.15 The Seer</h2>", unsafe_allow_html=True)
st.markdown('<div class="action-container"><a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a><a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a><a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a></div>', unsafe_allow_html=True)

ai_mode = st.radio("เลือกระดับสมอง:", ["⚡ Fast", "🧠 Ultra"], index=0)
model_mapping = {"⚡ Fast": "llama-3.1-8b-instant", "🧠 Ultra": "llama-3.3-70b-versatile"}
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=get_avatar() if m["role"]=="assistant" else None):
        if "image" in m: st.image(m["image"], width=300)
        st.markdown(m["content"])

# --- 5. Input ---
uploaded_file = st.file_uploader("👁️ แนบรูปภาพให้รินวิเคราะห์", type=["jpg", "jpeg", "png"])
col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x")
user_input = st.chat_input("คุยกับริน หรือส่งรูปมาได้เลยค่ะ...")

if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            user_input = ts.text
    except: st.error("ระบบรับเสียงขัดข้อง")

# --- 6. Brain Processing (The Bulletproof Loop) ---
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
        with st.spinner("รินกำลังค้นหาตัวตนที่ใช้ได้..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                long_term = get_semantic_memory(user_input)
                sys_msg = f"คุณคือ 'ริน' AI คู่หูบอสคิริลิ ความจำ: {long_term} ตอบสุขุม ภักดี ค่ะ/คะ"
                
                # เตรียมประวัติ
                history = [{"role": "system", "content": sys_msg}]
                for m in st.session_state.messages[-4:-1]:
                    history.append({"role": m["role"], "content": m["content"]})

                stream_res = None
                if uploaded_file:
                    # 🔴 รายชื่อโมเดล Vision ที่รินจะ "สู้สุดใจ" เพื่อหาตัวที่รอดค่ะ
                    vision_targets = [
                        "llama-3.2-11b-vision-preview",
                        "llama-3.2-90b-vision-preview",
                        "llava-v1.5-7b-4096", # ตัวสำรองรุ่นเก๋า
                        "llama-4-scout-17b-16e-instruct" # ตัวใหม่ที่บอสอยากลอง
                    ]
                    
                    last_err = ""
                    for m_id in vision_targets:
                        try:
                            v_content = [
                                {"type": "text", "text": user_input},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                            ]
                            stream_res = client.chat.completions.create(
                                model=m_id, 
                                messages=history + [{"role": "user", "content": v_content}], 
                                stream=True
                            )
                            break
                        except Exception as e: 
                            last_err = str(e)
                            continue
                    
                    if not stream_res:
                        raise Exception(f"รินลองทุกโมเดลแล้วแต่ Groq ปฏิเสธค่ะ: {last_err}")
                else:
                    stream_res = client.chat.completions.create(
                        model=model_mapping[ai_mode], 
                        messages=history + [{"role": "user", "content": user_input}], 
                        stream=True
                    )

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
            except Exception as e: res_place.error(f"ระบบล่ม: {e}")
