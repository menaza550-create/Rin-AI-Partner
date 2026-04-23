import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pinecone import Pinecone
from datetime import datetime
import os, base64, asyncio, edge_tts, re

# --- 1. UI & Persona Setup ---
st.set_page_config(page_title="Rin v38.11 Vision", layout="centered")

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
        memories = [f"{match['metadata']['text']}" for match in search_results['matches']]
        return "\n".join(memories) if memories else "ไม่มีข้อมูลในอดีต"
    except: return "Pinecone Disconnected"

def save_semantic_memory(u_input, r_output):
    try:
        pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])
        index = pc.Index("diana-memory")
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=u_input)
        record_id = datetime.now().strftime("%Y%m%d%H%M%S")
        index.upsert(vectors=[{"id": record_id, "values": res.data[0].embedding, "metadata": {"text": u_input, "reply": r_output}}])
    except: pass

# --- 3. Sidebar ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR_PATH): st.image(RIN_AVATAR_PATH, use_container_width=True)
    st.markdown("### 🏛️ Diana System Core")
    search_mode = st.toggle("🔍 โหมดสแกนเน็ต", value=False)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอแชท"): 
        st.session_state.messages = []
        st.rerun()

# --- 4. Main Menu & AI Selector ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v38.11 Vision</h2>", unsafe_allow_html=True)
st.markdown('<div class="action-container"><a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a><a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a><a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a><a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a></div>', unsafe_allow_html=True)

ai_mode = st.radio("เลือกระดับสมองของริน:", ["⚡ รวดเร็ว (Fast)", "🧠 วิเคราะห์ลึก (Ultra)"], index=0)
model_mapping = {"⚡ รวดเร็ว (Fast)": "llama-3.1-8b-instant", "🧠 วิเคราะห์ลึก (Ultra)": "llama-3.3-70b-versatile"}
selected_model_id = model_mapping[ai_mode]
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    curr_avatar = get_avatar() if m["role"] == "assistant" else None
    with st.chat_message(m["role"], avatar=curr_avatar):
        if "image" in m: st.image(m["image"], width=300)
        st.markdown(m["content"])

# --- 5. Input Layer ---
uploaded_file = st.file_uploader("👁️ แนบรูปภาพให้รินวิเคราะห์ (ถ้ามี)", type=["jpg", "jpeg", "png"])
col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
user_input = st.chat_input("คุยกับริน หรือสั่งวิเคราะห์รูปได้เลยค่ะบอส...")

if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            user_input = ts.text
    except: st.error("ระบบรับเสียงขัดข้อง")

# --- 6. Brain Processing ---
if user_input:
    user_msg_data = {"role": "user", "content": user_input}
    img_base64 = None
    if uploaded_file:
        img_bytes = uploaded_file.getvalue()
        user_msg_data["image"] = img_bytes
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    st.session_state.messages.append(user_msg_data)
    with st.chat_message("user"):
        if uploaded_file: st.image(uploaded_file, width=300)
        st.markdown(user_input)

    with st.chat_message("assistant", avatar=get_avatar()):
        response_placeholder = st.empty()
        with st.spinner("รินกำลังประมวลผล..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                long_term_ctx = get_semantic_memory(user_input)
                search_ctx = ""
                if search_mode and not uploaded_file:
                    try:
                        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                        res = tavily.search(query=user_input, max_results=2)
                        search_ctx = "\n[เน็ต]: " + " ".join([r['content'] for r in res['results']])
                    except: pass

                sys_msg = f"คุณคือ 'ริน' AI คู่หูบอสคิริลิ ความจำ: {long_term_ctx} {search_ctx} ตอบสุขุม ลงท้าย ค่ะ/คะ"
                messages_for_api = [{"role":"system","content":sys_msg}]
                for m in st.session_state.messages[-4:-1]:
                    messages_for_api.append({"role": m["role"], "content": m["content"]})

                # 🔴 แก้ไขจุดนี้: เปลี่ยนชื่อโมเดลเป็นรุ่น Vision ที่เสถียรที่สุดของ Groq
                if uploaded_file:
                    active_model = "llama-3.2-11b-vision-preview" # รินใส่รุ่นที่ระบบ Groq ปัจจุบันรองรับไว้ให้ค่ะ
                    messages_for_api.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_input},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                        ]
                    })
                else:
                    active_model = selected_model_id
                    messages_for_api.append({"role": "user", "content": user_input})

                stream_response = client.chat.completions.create(model=active_model, messages=messages_for_api, stream=True)
                answer = ""
                for chunk in stream_response:
                    if chunk.choices[0].delta.content is not None:
                        answer += chunk.choices[0].delta.content
                        response_placeholder.markdown(answer + "▌")
                
                clean_answer = re.sub(r'<.*?>', '', answer, flags=re.DOTALL).strip() if '<think>' in answer else answer
                response_placeholder.markdown(clean_answer)
                save_semantic_memory(user_input, clean_answer)
                st.session_state.messages.append({"role": "assistant", "content": clean_answer})

                if voice_on:
                    communicate = edge_tts.Communicate(clean_answer, "th-TH-PremwadeeNeural", rate="-10%", pitch="+2Hz")
                    asyncio.run(communicate.save("rin_voice.mp3"))
                    with open("rin_voice.mp3", "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                        st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
            except Exception as e: response_placeholder.error(f"Error: {str(e)}")
