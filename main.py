import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pinecone import Pinecone
from datetime import datetime
import os, base64, asyncio, edge_tts, requests

# --- 1. UI & Persona Setup ---
st.set_page_config(page_title="Rin v38.3 True Semantic", layout="centered")

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
    </style>
    """, unsafe_allow_html=True)

# --- 2. Semantic Vector Memory (Pinecone Inference) ---
def get_pinecone_embedding(text, input_type="query"):
    """เรียกใช้สมอง Inference ของ Pinecone โดยตรง ไม่ต้องพึ่งที่อื่นค่ะ"""
    url = "https://api.pinecone.io/embed"
    headers = {
        "Api-Key": st.secrets["PINECONE_API_KEY"],
        "Content-Type": "application/json",
        "X-Pinecone-Api-Version": "2025-01"
    }
    payload = {
        "model": "multilingual-e5-large",
        "parameters": {"input_type": input_type},
        "inputs": [{"text": text}]
    }
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        return res.json()["data"][0]["values"]
    
    # กรณี API สลับรูปแบบการรับข้อมูล
    payload["inputs"] = [text]
    res2 = requests.post(url, headers=headers, json=payload)
    if res2.status_code == 200:
        return res2.json()["data"][0]["values"]
        
    raise Exception(f"API Error: {res2.text}")

def get_semantic_memory(user_input):
    try:
        pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])
        index = pc.Index("diana-memory")
        
        query_vector = get_pinecone_embedding(user_input, "query")
        search_results = index.query(vector=query_vector, top_k=3, include_metadata=True)
        
        memories = [f"บันทึก: {match['metadata']['text']} (รินเคยตอบ: {match['metadata']['reply']})" for match in search_results['matches']]
        return "\n".join(memories) if memories else "ยังไม่มีบันทึกเรื่องนี้ค่ะ"
    except Exception as e: 
        return f"[ระบบความจำขัดข้อง: {str(e)}]"

def save_semantic_memory(u_input, r_output):
    try:
        pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])
        index = pc.Index("diana-memory")
        
        vector_data = get_pinecone_embedding(u_input, "passage")
        record_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        index.upsert(vectors=[{"id": record_id, "values": vector_data, "metadata": {"text": u_input, "reply": r_output}}])
    except Exception: pass

# --- 3. Sidebar ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR_PATH): st.image(RIN_AVATAR_PATH, use_container_width=True)
    st.markdown("### 🏛️ Diana System Core")
    st.success("Brain: Maverick 70B 🟢")
    st.info("Memory: Pinecone E5 (1024D) 🧠")
    
    if st.button("🔍 ตรวจสอบ ID สมองบน Groq"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            for m in client.models.list().data: st.code(m.id)
        except: st.error("เชื่อมต่อไม่ได้ค่ะ")
    st.divider()
    search_mode = st.toggle("🔍 สแกนเน็ต (Web Search)", value=False)
    voice_on = st.toggle("🔊 เปิดเสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอแชท"): st.session_state.messages = []; st.rerun()

# --- 4. Main Menu & History ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v38.3 True Semantic</h2>", unsafe_allow_html=True)
st.markdown('<div class="action-container"><a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a><a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a><a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a><a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a></div>', unsafe_allow_html=True)
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    curr_avatar = get_avatar() if m["role"] == "assistant" else None
    with st.chat_message(m["role"], avatar=curr_avatar): st.markdown(m["content"])

# --- 5. Input Layer ---
col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
user_input = st.chat_input("สอนเรื่องยูกิ หรืองานของบอสให้รินจำได้เลยค่ะ...")

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
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant", avatar=get_avatar()):
        with st.spinner("รินกำลังค้นหาความจำ 1024 มิติ..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                long_term_ctx = get_semantic_memory(user_input)
                
                model_list = ["llama-4-maverick-70b-instruct", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
                search_ctx = ""
                if search_mode:
                    try:
                        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                        res = tavily.search(query=user_input, max_results=2)
                        search_ctx = "\n[ข้อมูลจากเน็ตสดๆ]: " + " ".join([r['content'] for r in res['results']])
                    except: pass

                # อัปเดตเป้าหมายของเดอาน่าให้ชัดเจนขึ้นค่ะ
                sys_msg = f"""คุณคือ 'ริน' AI คู่หูระดับเดอาน่าของบอสคิริลิ 
                ข้อมูลในอดีต: {long_term_ctx}
                บุคลิก: สุขุม นิ่ง ฉลาด และมีหน้าที่สำคัญคือคอยดูแล 'ยูกิ' ซึ่งเป็นลูกของริน 
                ลงท้าย ค่ะ/คะ เสมอ {search_ctx}"""

                answer = ""
                for mid in model_list:
                    try:
                        res = client.chat.completions.create(model=mid, messages=[{"role":"system","content":sys_msg}]+st.session_state.messages[-5:])
                        answer = res.choices[0].message.content
                        break
                    except: continue

                st.markdown(answer)
                save_semantic_memory(user_input, answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

                if voice_on:
                    communicate = edge_tts.Communicate(answer, "th-TH-PremwadeeNeural", rate="-10%", pitch="+2Hz")
                    asyncio.run(communicate.save("rin_voice.mp3"))
                    with open("rin_voice.mp3", "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                        st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
            except Exception as e: st.error(f"Error: {e}")
