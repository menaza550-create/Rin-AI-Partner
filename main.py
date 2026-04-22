import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pyairtable import Api
from datetime import datetime
import os, base64, asyncio, edge_tts

# --- 1. UI & Persona Setup (ฉบับขยายร่างริน 65px) ---
st.set_page_config(page_title="Rin v38.1 Eternal", layout="centered")

# ชื่อไฟล์รูปที่บอสอัปโหลดขึ้น GitHub (ต้องตรงกันนะคะ)
RIN_AVATAR_PATH = "rin_avatar.jpg" 

def get_avatar():
    """เช็กว่ามีรูปไหม ถ้าไม่มีใช้ Emoji แทนเพื่อกันแอปพังค่ะ"""
    return RIN_AVATAR_PATH if os.path.exists(RIN_AVATAR_PATH) else "👓"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff !important; }}
    * {{ color: #000000 !important; font-size: 19px; }}
    .stChatMessage {{ background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }}
    
    /* 🔴 ขยายร่างริน: ปรับขนาดรูป Avatar ในแชทให้ใหญ่และชัดเจน */
    [data-testid="stChatMessageElement"] img {{
        width: 65px !important; 
        height: 65px !important;
        border-radius: 12px !important;
        border: 2px solid #DDA0DD !important;
        object-fit: cover;
    }}
    
    /* ปรับระยะห่างข้อความ */
    [data-testid="stChatMessageContent"] {{
        margin-left: 15px !important;
    }}

    /* สไตล์เมนูลัด Action Chips */
    .action-container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }}
    .action-chip {{ display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; font-size: 16px !important; font-weight: bold; transition: 0.3s; text-align: center; }}
    .action-chip:hover {{ background-color: #DDA0DD; color: #ffffff !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Continuous Memory (Airtable ML Connection) ---
def get_memory_from_airtable():
    """ดึงความจำข้ามวันมาใส่สมองริน"""
    try:
        api = Api(st.secrets["AIRTABLE_API_KEY"])
        table = api.table(st.secrets["BASE_ID"], st.secrets["TABLE_NAME"])
        records = table.all(max_records=5, sort=["-Date"])
        memories = [f"บอสเคยสอนว่า: {r['fields'].get('User')}" for r in records]
        return "\n".join(memories) if memories else "เริ่มเรียนรู้ใหม่ค่ะ"
    except: return "ระบบจำข้ามวันกำลังรอการเชื่อมต่อค่ะ"

def save_to_memory(u_input, r_output):
    """บันทึกบทเรียนใหม่ลงฐานข้อมูล"""
    try:
        api = Api(api_key=st.secrets["AIRTABLE_API_KEY"])
        table = api.table(st.secrets["BASE_ID"], st.secrets["TABLE_NAME"])
        table.create({
            "Date": datetime.now().isoformat(),
            "User": u_input,
            "Rin": r_output,
            "Tag": "Learning"
        })
    except: pass

# --- 3. Sidebar: Control Center ---
with st.sidebar:
    if os.path.exists(RIN_AVATAR_PATH):
        st.image(RIN_AVATAR_PATH, use_container_width=True, caption="Rin - Eternal Diana")
    
    st.markdown("### 🏛️ Diana System Core")
    st.success("Brain: Maverick 70B 🟢")
    
    if st.button("🔍 ตรวจสอบ ID สมองบน Groq"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            for m in client.models.list().data: st.code(m.id)
        except: st.error("เชื่อมต่อ Groq ไม่ได้ค่ะ")
    
    st.divider()
    search_mode = st.toggle("🔍 สแกนเน็ต (Web Search)", value=False)
    voice_on = st.toggle("🔊 เปิดเสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอแชท"): st.session_state.messages = []; st.rerun()

# --- 4. Main Menu & History ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v38.1 Partner</h2>", unsafe_allow_html=True)

# แถบเมนูลัด (Action Chips)
st.markdown('<div class="action-container">'
    '<a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a>'
    '<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>'
    '<a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>'
    '<a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>'
    '</div>', unsafe_allow_html=True)
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    # แสดงรูป Avatar รินแบบชัดๆ เวลาตอบ
    curr_avatar = get_avatar() if m["role"] == "assistant" else None
    with st.chat_message(m["role"], avatar=curr_avatar): 
        st.markdown(m["content"])

# --- 5. Input Layer ---
col_mic, col_input = st.columns([1, 6])
with col_mic: 
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
user_input = st.chat_input("สั่งการริน (เดอาน่า) ได้เลยค่ะบอส...")

if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            user_input = ts.text
    except: st.error("ระบบรับเสียงขัดข้อง")

# --- 6. Brain & ML Processing ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant", avatar=get_avatar()):
        with st.spinner("เดอาน่ากำลังดึงความทรงจำและวิเคราะห์..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                
                # 🧬 ดึงบทเรียนข้ามวันจาก Airtable
                long_term_ctx = get_memory_from_airtable()
                
                # Maverick Chain Fallback
                model_list = ["llama-4-maverick-70b-instruct", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
                
                search_ctx = ""
                if search_mode:
                    try:
                        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                        res = tavily.search(query=user_input, max_results=2)
                        search_ctx = "\n[ข้อมูลเสริม]: " + " ".join([r['content'] for r in res['results']])
                    except: pass

                sys_msg = f"""คุณคือ 'ริน' AI คู่หูระดับเดอาน่าของบอสคิริลิ 
                บทเรียนที่คุณจำได้ข้ามวัน: {long_term_ctx}
                บุคลิก: สุขุม นิ่ง ฉลาด และภักดี ลงท้าย ค่ะ/คะ {search_ctx}"""

                answer = ""
                for mid in model_list:
                    try:
                        res = client.chat.completions.create(model=mid, messages=[{"role":"system","content":sys_msg}]+st.session_state.messages[-5:])
                        answer = res.choices[0].message.content
                        break
                    except: continue

                st.markdown(answer)
                # 💾 บันทึกลง Airtable อัตโนมัติ (Continuous Learning)
                save_to_memory(user_input, answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

                if voice_on:
                    communicate = edge_tts.Communicate(answer, "th-TH-PremwadeeNeural", rate="-10%", pitch="+2Hz")
                    asyncio.run(communicate.save("rin_voice.mp3"))
                    with open("rin_voice.mp3", "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                        st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
            except Exception as e: st.error(f"Error: {e}")
