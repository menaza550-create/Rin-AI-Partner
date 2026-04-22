import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pyairtable import Api
from datetime import datetime
import os, base64, asyncio, edge_tts
from PIL import Image
import io

# --- 1. UI & Styling ---
st.set_page_config(page_title="Rin v34.9 Partner", layout="centered")

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

# --- 2. Core Functions ---
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def play_audio_hidden(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)

async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-10%", pitch="+2Hz")
    await communicate.save("rin_voice.mp3")

@st.cache_data(ttl=300)
def fetch_lunc_price():
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        res = tavily.search(query="LUNC price USD today", max_results=1)
        return res["results"][0]["content"][:120]
    except: return "ดึงข้อมูลไม่ได้ค่ะ"

# --- 3. Sidebar ---
with st.sidebar:
    st.markdown("### 📊 Diana System Status")
    st.markdown(f'<div class="crypto-card"><b>LUNC Today:</b><br>{fetch_lunc_price()}</div>', unsafe_allow_html=True)
    st.success("Vision 90B & Brain 70B: Online 🟢")
    st.divider()
    search_mode = st.toggle("🔍 โหมดหาข้อมูล (Web Search)", value=False)
    voice_on = st.toggle("🔊 เปิดเสียงเลขา", value=True)
    if st.button("🗑️ ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

# --- 4. Main Page ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v34.9 Partner</h2>", unsafe_allow_html=True)
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

# --- 5. Input Layer ---
uploaded_file = st.file_uploader("ส่งรูปภาพให้ริน (บิล/กราฟ/โฆษณา)", type=["jpg", "jpeg", "png"])
col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
prompt = st.chat_input("สั่งการรินได้เลยค่ะบอส...")

# เตรียมตัวแปรให้พร้อม ป้องกัน NameError 👓
final_input = None
user_content = []

if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            final_input = ts.text
    except: st.error("ไมค์ขัดข้อง")
elif prompt: 
    final_input = prompt

# --- 6. Brain Processing (Diana ML Mode) ---
if final_input or uploaded_file:
    # สร้างโครงสร้างข้อมูลสำหรับส่งให้ Groq
    if final_input: 
        user_content.append({"type": "text", "text": final_input})
    
    if uploaded_file:
        base64_image = encode_image(uploaded_file)
        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})
        st.image(uploaded_file, caption="วิเคราะห์รูปภาพ...", width=300)

    # แสดงผลฝั่งผู้ใช้
    display_msg = final_input if final_input else "*(ส่งรูปภาพให้รินวิเคราะห์)*"
    st.session_state.messages.append({"role": "user", "content": display_msg})
    with st.chat_message("user"): st.markdown(display_msg)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("Diana Mode กำลังประมวลผล..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                # เลือก Model ตามความเหมาะสม (Vision vs Chat)
                model_to_use = "llama-3.2-90b-vision-preview" if uploaded_file else "llama-3.3-70b-versatile"
                
                # ดึงข้อมูลเสริมถ้าเปิดโหมดค้นหา
                search_info = ""
                if search_mode and final_input:
                    tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                    s_res = tavily.search(query=final_input, max_results=2)
                    search_info = "\nข้อมูลเสริม: " + " ".join([r['content'] for r in s_res['results']])

                sys_msg = f"คุณคือ 'ริน' AI คู่หูระดับ Diana ของบอสคิริลิ แห่งพัทยา ดูแลสุขภาพ การเงิน และโฆษณา บุคลิกสุขุม นิ่ง ฉลาด ลงท้าย ค่ะ/คะ เสมอ {search_info}"

                response = client.chat.completions.create(
                    model=model_to_use,
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": user_content}],
                    max_tokens=1024
                )
                answer = response.choices[0].message.content
                
                st.markdown(answer)
                if voice_on:
                    asyncio.run(make_voice(answer))
                    play_audio_hidden("rin_voice.mp3")
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {str(e)}")
