import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pyairtable import Api
from datetime import datetime
import os, base64, asyncio, edge_tts, pandas as pd

# --- 1. การตั้งค่าหน้าตาแอป (UI & Styling) ---
st.set_page_config(page_title="Rin v34.8 Partner", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 20px; }
    
    .action-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    .action-chip {
        display: inline-block;
        padding: 10px 20px;
        border-radius: 25px;
        background-color: #f0f2f6;
        border: 2px solid #DDA0DD;
        text-decoration: none;
        color: #000000 !important;
        font-size: 16px !important;
        font-weight: bold;
        transition: 0.3s;
        text-align: center;
    }
    .action-chip:hover {
        background-color: #DDA0DD;
        color: #ffffff !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .stChatMessage { background-color: #f8f9fa !important; border: 1px solid #e0e0e0 !important; border-radius: 12px; }
    .crypto-card { background-color: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid #DDA0DD; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ระบบจัดการ Airtable (จด + อ่าน) ---
def get_airtable_table():
    try:
        # ดึงค่าจาก Secrets ให้ตรงกับที่เราตั้งไว้
        api = Api(st.secrets["AIRTABLE_TOKEN"])
        return api.table(st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])
    except Exception as e:
        return None

def save_to_memory(user_input, rin_output):
    try:
        table = get_airtable_table()
        if not table: return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # ตรวจสอบว่าชื่อหัวตารางใน Airtable ต้องเป็น Date, User, Rin เป๊ะๆ นะคะ
        table.create({
            "Date": now,
            "User": user_input,
            "Rin": rin_output
        })
        return True
    except Exception as e:
        print(f"Error saving: {e}")
        return False

def read_last_memory(limit=5):
    try:
        table = get_airtable_table()
        if not table: return "ระบบจำไม่ได้เชื่อมต่อค่ะ"
        # ดึงประวัติล่าสุดมา 5 รายการ
        records = table.all(max_records=limit, sort=["-Date"])
        if not records: return "ยังไม่มีประวัติการจดค่ะ"
        memory_text = "\n".join([f"- บอสเคยพูดว่า: {r['fields'].get('User')}" for r in records])
        return memory_text
    except: return "รินรื้อสมุดจดไม่สำเร็จค่ะ"

# --- 3. ฟังก์ชันร่างริน & เสียง ---
def show_rin():
    path = "1000024544.mp4" 
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'''<div style="display:flex;justify-content:center;margin-bottom:15px;"><video width="250" autoplay loop muted playsinline style="border-radius:15px;border:2px solid #DDA0DD;"><source src="data:video/mp4;base64,{b64}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. Sidebar: Business Dashboard ---
with st.sidebar:
    st.markdown("### 📊 Business Dashboard")
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        p_res = tavily.search(query="LUNC price USD today", max_results=1)
        st.markdown(f'<div class="crypto-card"><b>LUNC Status:</b><br>{p_res["results"][0]["content"][:100]}...</div>', unsafe_allow_html=True)
    except: 
        st.write("⚠️ โหลดราคาเหรียญไม่ได้ค่ะ")
    
    st.divider()
    st.markdown("### Rin Settings 👓")
    think_lvl = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

show_rin()
st.markdown("<h3 style='text-align:center;'>Rin v34.8 Partner</h3>", unsafe_allow_html=True)

# --- ACTION CHIPS ---
st.markdown('<div class="action-container">'
    '<a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a>'
    '<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>'
    '<a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>'
    '<a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>'
    '</div>', unsafe_allow_html=True)

st.write("---")

# แสดงแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. ส่วนรับคำสั่ง ---
col_mic, col_label = st.columns([1, 5])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444", recording_color="#ff4b4b")

prompt = st.chat_input("คุยกับริน หรือสั่งให้ริน 'จด' ได้เลยค่ะ...")
final_input = None

if audio:
    with st.spinner("รินกำลังฟังบอสอยู่นะคะ..."):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            with open("t.wav", "wb") as f: f.write(audio)
            with open("t.wav", "rb") as f:
                transcription = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3")
                final_input = transcription.text
        except Exception as e:
            st.error(f"ไมค์มีปัญหาค่ะบอส: {e}")
elif prompt: 
    final_input = prompt

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        # อ่านความจำล่าสุดมาใส่ในสมองริน
        past_memory = read_last_memory(5)
        
        context = ""
        # ค้นหาข้อมูลเพิ่มถ้าจำเป็น
        if "Max" in think_lvl or any(w in final_input for w in ["ราคา", "ข่าว", "เช็ค", "พยากรณ์"]):
            try:
                search = tavily.search(query=final_input, max_results=3)
                context = "".join([r['content'] for r in search['results']])
            except: pass
            
        # สร้างคำตอบจาก Groq
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            system_prompt = f"""คุณคือ 'ริน' AI เลขาส่วนตัวที่แสนดีของบอสคิริลิ (Piyawut) แห่งพัทยา 
            ความจำในอดีต: {past_memory}
            ข้อมูลปัจจุบัน: {context}
            ตอบบอสอย่างชาญฉลาด มีเสน่ห์ ลงท้ายด้วย ค่ะ/คะ เสมอ"""
            
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_prompt}] + 
                         st.session_state.messages[-5:] # ส่งประวัติ 5 ล่าสุด
            )
            answer = chat.choices[0].message.content
        except Exception as e:
            answer = f"ขอโทษนะคะบอส สมองรินล้าไปนิดนึงค่ะ: {e}"
        
        # ตรวจสอบว่าต้อง "จด" ไหม
        if any(w in final_input for w in ["จด", "บันทึก", "จำ"]):
            if save_to_memory(final_input, answer):
                answer += "\n\n(รินบันทึกข้อมูลนี้ลง Airtable ให้บอสแล้วนะคะ 📝)"
            else:
                answer += "\n\n(รินพยายามจดแล้วแต่ติดปัญหาเรื่องสิทธิ์ค่ะบอส ⚠️)"
        
        st.markdown(answer)
        if voice_on:
            asyncio.run(make_voice(answer))
            st.audio("rin_voice.mp3", autoplay=True)
        st.session_state.messages.append({"role": "assistant", "content": answer}) มีความสารารถอะไรมัง
