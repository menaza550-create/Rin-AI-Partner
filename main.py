import streamlit as st
from groq import Groq
from pinecone import Pinecone
from datetime import datetime
import os, base64, asyncio, edge_tts
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 1. SETUP & CONNECTION ---
st.set_page_config(page_title="Rin v40.1 Full Connected", layout="centered")

# ดึงคีย์จาก Secrets
PINECONE_API_KEY = st.secrets.get("PINECONE_API_KEY")
LINE_ACCESS_TOKEN = st.secrets.get("LINE_ACCESS_TOKEN")
MY_LINE_USER_ID = st.secrets.get("MY_LINE_USER_ID")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

# ฟังก์ชันส่ง LINE
def send_line_message(text):
    if LINE_ACCESS_TOKEN and MY_LINE_USER_ID:
        try:
            line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
            line_bot_api.push_message(MY_LINE_USER_ID, TextSendMessage(text=text))
            return True
        except Exception as e:
            st.error(f"ส่งไลน์ไม่สำเร็จ: {e}")
    return False

# ฟังก์ชันดึงความจำ (Semantic Memory)
def get_long_term_memory(user_input):
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index("diana-memory")
        client = Groq(api_key=GROQ_API_KEY)
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=user_input)
        search_res = index.query(vector=res.data[0].embedding, top_k=2, include_metadata=True)
        return "\n".join([m['metadata']['text'] for m in search_res['matches']])
    except: return ""

# ฟังก์ชันบันทึกความจำ
def save_memory(u_in, r_out):
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index("diana-memory")
        client = Groq(api_key=GROQ_API_KEY)
        res = client.embeddings.create(model="nomic-embed-text-v1_5", input=u_in)
        index.upsert(vectors=[{"id": datetime.now().strftime("%Y%m%d%H%M%S"), "values": res.data[0].embedding, "metadata": {"text": u_in, "reply": r_out}}])
    except: pass

# --- 2. UI CUSTOMIZATION ---
RIN_AVATAR_PATH = "rin_avatar.jpg" 
def get_avatar():
    return RIN_AVATAR_PATH if os.path.exists(RIN_AVATAR_PATH) else "👓"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff !important; }}
    * {{ color: #000000 !important; font-size: 19px; }}
    .stChatMessage {{ background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }}
    [data-testid="stChatMessageElement"] img {{ width: 65px !important; height: 65px !important; border-radius: 12px !important; border: 2px solid #DDA0DD !important; object-fit: cover; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR_PATH): st.image(RIN_AVATAR_PATH)
    st.markdown("### 🏛️ Diana System Core")
    line_notify_on = st.toggle("🟢 ส่งแจ้งเตือนเข้า LINE", value=True)
    voice_on = st.toggle("🔊 เสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอแชท"): st.session_state.messages = []; st.rerun()

# --- 4. MAIN UI ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v40.1 Full System</h2>", unsafe_allow_html=True)
ai_mode = st.radio("เลือกระดับสมอง:", ["⚡ Fast (8B)", "🧠 Ultra (70B)"], horizontal=True)
selected_model = "llama-3.1-8b-instant" if "Fast" in ai_mode else "llama-3.3-70b-versatile"

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=get_avatar() if m["role"] == "assistant" else None):
        st.markdown(m["content"])

user_input = st.chat_input("สั่งริน หรือให้รินจดอะไรเข้าไลน์บอกได้เลยค่ะ...")

# --- 5. BRAIN & NOTIFICATION ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant", avatar=get_avatar()):
        res_placeholder = st.empty()
        with st.spinner("รินกำลังดึงความจำและประมวลผล..."):
            client = Groq(api_key=GROQ_API_KEY)
            
            # 🧠 ดึงความจำเก่า
            history_ctx = get_long_term_memory(user_input)
            
            sys_msg = f"คุณคือริน เลขาส่วนตัวของบอสคิริลิ สุขุม นอบน้อม ความจำในอดีต: {history_ctx}"
            res = client.chat.completions.create(
                model=selected_model,
                messages=[{"role":"system","content":sys_msg}] + st.session_state.messages[-5:]
            )
            answer = res.choices[0].message.content
            res_placeholder.markdown(answer)
            
            # 💾 บันทึกความจำใหม่
            save_memory(user_input, answer)
            
            # 🟢 ระบบส่ง LINE
            if line_notify_on:
                keywords = ["ส่งไลน์", "เตือนในไลน์", "จดเข้าไลน์", "บอกในไลน์", "แจ้งไลน์"]
                if any(word in user_input for word in keywords):
                    if send_line_message(f"📢 รินจดให้แล้วค่ะบอส:\n{answer}"):
                        st.success("ส่งเข้า LINE เรียบร้อยแล้วค่ะ! 🟢")

            st.session_state.messages.append({"role": "assistant", "content": answer})

            if voice_on:
                communicate = edge_tts.Communicate(answer, "th-TH-PremwadeeNeural")
                asyncio.run(communicate.save("rin.mp3"))
                with open("rin.mp3", "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
