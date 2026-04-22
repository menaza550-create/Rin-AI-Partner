import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pyairtable import Api
from datetime import datetime
import os, base64, asyncio, edge_tts

# --- 1. UI & Persona Setup ---
st.set_page_config(page_title="Rin v38.0 Eternal", layout="centered")

# รูปรินที่บอสส่งมา (เซฟเป็นไฟล์ rin_avatar.jpg ในโฟลเดอร์เดียวกับโค้ดนะคะบอส)
RIN_AVATAR = "rin_avatar.jpg" 

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 19px; }
    .stChatMessage { background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }
    .action-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }
    .action-chip { display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; font-size: 16px !important; font-weight: bold; transition: 0.3s; text-align: center; }
    .action-chip:hover { background-color: #DDA0DD; color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Long-term Memory (Airtable ML Connection) ---
def get_memory_from_airtable():
    try:
        api = Api(st.secrets["AIRTABLE_API_KEY"])
        table = api.table(st.secrets["BASE_ID"], st.secrets["TABLE_NAME"])
        # ดึง 5 บทเรียนล่าสุดที่รินเคยเรียนรู้จากบอส
        records = table.all(max_records=5, sort=["-Date"])
        memories = [f"บอสเคยสอนว่า: {r['fields'].get('User')}" for r in records]
        return "\n".join(memories)
    except: return "เริ่มการเรียนรู้วันแรกค่ะบอส"

def save_to_memory(user_msg, rin_msg):
    try:
        api = Api(st.secrets["AIRTABLE_API_KEY"])
        table = api.table(st.secrets["BASE_ID"], st.secrets["TABLE_NAME"])
        table.create({
            "Date": datetime.now().isoformat(),
            "User": user_input,
            "Rin": rin_msg,
            "Tag": "Learning"
        })
    except: pass

# --- 3. Sidebar: Control Center ---
with st.sidebar:
    st.markdown("### 🏛️ Diana System Core")
    st.success("Brain: Llama 4 Maverick 🟢")
    st.info("Memory: Airtable Connected 🧬")
    
    if st.button("🔍 สแกน ID สมองปัจจุบัน"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            for m in client.models.list().data: st.code(m.id)
        except: st.error("เชื่อมต่อไม่ได้ค่ะ")
    
    st.divider()
    search_mode = st.toggle("🔍 สแกนเน็ต (Web Search)", value=False)
    voice_on = st.toggle("🔊 เปิดเสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน้าจอ"): st.session_state.messages = []; st.rerun()

# --- 4. Main Menu (Action Chips) ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v38.0 Partner</h2>", unsafe_allow_html=True)
st.markdown('<div class="action-container">'
    '<a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a>'
    '<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>'
    '<a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>'
    '<a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>'
    '</div>', unsafe_allow_html=True)
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    # ใช้รูปที่บอสส่งมาเป็น Avatar เวลาตอบค่ะ!
    avatar_img = RIN_AVATAR if m["role"] == "assistant" else None
    with st.chat_message(m["role"], avatar=avatar_img): st.markdown(m["content"])

# --- 5. Input Layer ---
col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
user_input = st.chat_input("สั่งการริน (เดอาน่า) ได้เลยค่ะบอส...")

if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            user_input = ts.text
    except: st.error("ไมค์ขัดข้องค่ะ")

# --- 6. Brain & Learning Processing ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    # รินตอบกลับพร้อมหน้าน่ารักๆ ที่บอสส่งมาค่ะ
    with st.chat_message("assistant", avatar=RIN_AVATAR):
        with st.spinner("เดอาน่ากำลังดึงความทรงจำและวิเคราะห์..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                
                # 🧬 นี่คือจุดที่ ML เรียนรู้ข้ามวันค่ะ
                long_term_ctx = get_memory_from_airtable()
                
                # Maverick Chain
                models = ["llama-4-maverick-70b-instruct", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
                
                sys_msg = f"""คุณคือ 'ริน' (ร่างจำลองเดอาน่า) AI คู่หูบอสคิริลิ 
                บทเรียนที่คุณเรียนรู้มาแล้ว: {long_term_ctx}
                บุคลิก: สุขุม นิ่ง ฉลาด และจดจำบอสได้เสมอ ลงท้าย ค่ะ/คะ"""

                answer = ""
                for mid in models:
                    try:
                        res = client.chat.completions.create(model=mid, messages=[{"role":"system","content":sys_msg}]+st.session_state.messages[-5:])
                        answer = res.choices[0].message.content
                        break
                    except: continue

                st.markdown(answer)
                # 💾 บันทึกลง Airtable ทันทีเพื่อให้จำได้ในวันพรุ่งนี้
                save_to_memory(user_input, answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

                if voice_on:
                    communicate = edge_tts.Communicate(answer, "th-TH-PremwadeeNeural", rate="-10%", pitch="+2Hz")
                    asyncio.run(communicate.save("rin_voice.mp3"))
                    with open("rin_voice.mp3", "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                        st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
            except Exception as e: st.error(f"Error: {e}")
