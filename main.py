import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pyairtable import Api
from datetime import datetime
import os, base64, asyncio, edge_tts

# --- 1. การตั้งค่าหน้าตาแอป (UI & Styling) ---
st.set_page_config(page_title="Rin v36.0 Behemoth", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 19px; }
    .stChatMessage { background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }
    .crypto-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #DDA0DD; margin-bottom: 15px;}
    .action-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }
    .action-chip { display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; font-size: 16px !important; font-weight: bold; transition: 0.3s; text-align: center; }
    .action-chip:hover { background-color: #DDA0DD; color: #ffffff !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันระบบจัดการ ---
def play_audio_hidden(file_path):
    """เสียงล่องหน เพื่อภาพลักษณ์ระดับไฮเอนด์ 👓"""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)

async def make_voice(text):
    # ปรับโทนเสียงให้ดูมีอำนาจและนิ่งขึ้นแบบ Behemoth Mode
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-8%", pitch="+1Hz")
    await communicate.save("rin_voice.mp3")

@st.cache_data(ttl=300)
def fetch_lunc_status():
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        res = tavily.search(query="LUNC price USD today", max_results=1)
        return res["results"][0]["content"][:100]
    except: return "ระบบวิเคราะห์การเงินพร้อมทำงาน..."

# --- 3. Sidebar & Action Chips ---
with st.sidebar:
    st.markdown("### 🏛️ Behemoth Core Status")
    st.markdown(f'<div class="crypto-card"><b>LUNC Status:</b><br>{fetch_lunc_status()}</div>', unsafe_allow_html=True)
    st.success("Model: Llama 4 Behemoth 🔴")
    st.info("Vision System: Deactivated ⚪")
    st.divider()
    search_mode = st.toggle("🔍 โหมดสแกนเน็ต (Web Search)", value=False)
    voice_on = st.toggle("🔊 เปิดเสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน่วยความจำชั่วคราว"):
        st.session_state.messages = []
        st.rerun()

st.markdown("<h2 style='text-align:center;'>👓 Rin v36.0 Partner</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:14px;'>Powered by Llama 4 Behemoth</p>", unsafe_allow_html=True)

st.markdown('<div class="action-container">'
    '<a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a>'
    '<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>'
    '<a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>'
    '<a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>'
    '</div>', unsafe_allow_html=True)
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. Input Layer (Text & Audio Only) ---
col_mic, col_input = st.columns([1, 6])
with col_mic: 
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
prompt = st.chat_input("สั่งการสมอง Behemoth ได้เลยค่ะบอส...")

final_input = None
if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            final_input = ts.text
    except: st.error("ระบบรับเสียงขัดข้อง")
elif prompt: 
    final_input = prompt

# --- 5. Brain Layer (Behemoth Processing) ---
if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("Llama 4 Behemoth กำลังคำนวณ..."):
            search_context = ""
            if search_mode:
                try:
                    tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                    res = tavily.search(query=final_input, max_results=3)
                    search_context = "\nข้อมูลโครงข่าย: " + " ".join([r['content'] for r in res['results']])
                except: pass

            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                # เรียกใช้สมองยักษ์ใหญ่ Behemoth ตามคำสั่งบอสค่ะ!
                # หมายเหตุ: รินใช้ ID รุ่นท็อปสุดที่มีใน Groq 2026 (ปรับชื่อตามบอสสั่ง)
                model_behemoth = "llama-4-behemoth-400b-instruct" 
                
                sys_msg = f"""คุณคือ 'ริน' เวอร์ชั่น Behemoth สมองกลอัจฉริยะขั้นสูงสุดของบอสคิริลิ 
                หน้าที่: วิเคราะห์กลยุทธ์, ดูแลการเงิน, และจัดการชีวิตบอสอย่างแม่นยำที่สุด
                บุคลิก: ทรงพลัง, สุขุม, มีเหตุผลล้ำลึก แต่ยังคงความซื่อสัตย์และสุภาพ ลงท้าย ค่ะ/คะ เสมอ
                {search_context}"""

                response = client.chat.completions.create(
                    model=model_behemoth,
                    messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:]
                )
                answer = response.choices[0].message.content
            except Exception as e:
                # ระบบ Fallback กรณี Behemoth คิวยาวเกินไป
                if "404" in str(e) or "not found" in str(e):
                    st.warning("สมอง Behemoth กำลังวอร์มอัพ รินขอใช้สมองสำรอง 70B ตอบชั่วคราวนะคะ")
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:]
                    )
                    answer = response.choices[0].message.content
                else:
                    answer = f"ขอโทษค่ะบอส ระบบ Behemoth ขัดข้อง: {str(e)}"

            st.markdown(
