import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pyairtable import Api
from datetime import datetime
import os, base64, asyncio, edge_tts

# --- 1. การตั้งค่าหน้าตาแอป (UI & Styling) ---
st.set_page_config(page_title="Rin v34.8 Partner", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 19px; }
    .stChatMessage { background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }
    .crypto-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #DDA0DD; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันช่วยเพิ่มความเร็ว (Caching) ---
@st.cache_data(ttl=300) # จำราคาไว้ 5 นาที ไม่ต้องโหลดใหม่ทุกรอบ
def fetch_lunc_price():
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        res = tavily.search(query="LUNC price USD today", max_results=1)
        return res["results"][0]["content"][:120]
    except:
        return "ไม่สามารถดึงข้อมูลราคาได้ในขณะนี้ค่ะ"

def get_airtable_table():
    try:
        api = Api(st.secrets["AIRTABLE_TOKEN"])
        return api.table(st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])
    except:
        return None

@st.cache_data(ttl=60) # จำความจำล่าสุดไว้ 1 นาที
def read_last_memory(limit=5):
    try:
        table = get_airtable_table()
        if not table: return "ไม่ได้เชื่อมต่อความจำค่ะ"
        records = table.all(max_records=limit, sort=["-Date"])
        if not records: return "ไม่มีบันทึกเก่าค่ะ"
        return "\n".join([f"- บอสเคยพูดว่า: {r['fields'].get('User')}" for r in records])
    except: return "รื้อสมุดจดไม่สำเร็จค่ะ"

async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-15%", pitch="+2Hz")
    await communicate.save("rin_voice.mp3")

# --- 3. Sidebar & Dashboard ---
with st.sidebar:
    st.markdown("### 📊 Business Status")
    lunc_info = fetch_lunc_price()
    st.markdown(f'<div class="crypto-card"><b>LUNC Status:</b><br>{lunc_info}...</div>', unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### Rin Settings 👓")
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

st.markdown("<h2 style='text-align:center;'>👓 Rin v34.8 Partner</h2>", unsafe_allow_html=True)
st.write("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. การประมวลผลคำสั่ง ---
col_mic, col_input = st.columns([1, 6])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")

prompt = st.chat_input("สั่งการรินได้เลยค่ะบอส...")
final_input = None

if audio:
    with st.spinner("รินฟังอยู่ค่ะ..."):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            with open("temp.wav", "wb") as f: f.write(audio)
            with open("temp.wav", "rb") as f:
                ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
                final_input = ts.text
        except: st.error("ไมค์ขัดข้องค่ะ")
elif prompt:
    final_input = prompt

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"):
        st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินกำลังคิด..."):
            memory = read_last_memory(3)
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                sys_msg = f"""คุณคือ 'ริน' เลขาส่วนตัวของบอสคิริลิ (Piyawut) แห่งพัทยา
                หน้าที่: ดูแลสุขภาพ, บิลค่าน้ำไฟ, ค่าใช้จ่าย และตรวจสอบความถูกต้อง
                บุคลิก: ฉลาด อบอุ่น สุภาพ ลงท้าย 'ค่ะ/คะ' เสมอ
                ความจำล่าสุด: {memory}"""
                
                chat = client.chat.completions.create(
                    model="llama-3.3-70b-versatile", # ใช้สมองตัวท็อปสุดที่เสถียรของ Groq 
                    messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:]
                )
                answer = chat.choices[0].message.content
            except Exception as e:
                answer = f"ขอโทษค่ะบอส สมองรินล้านิดหน่อย: {str(e)}"

            st.markdown(answer)
            
            if voice_on:
                asyncio.run(make_voice(answer))
                st.audio("rin_voice.mp3", autoplay=True)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})

            # ระบบบันทึกอัตโนมัติถ้าบอสสั่ง
            if any(w in final_input for w in ["จด", "บันทึก", "จำ"]):
                table = get_airtable_table()
                if table:
                    table.create({"Date": datetime.now().isoformat(), "User": final_input, "Rin": answer})
                    st.toast("จดลง Airtable แล้วค่ะ 📝")
