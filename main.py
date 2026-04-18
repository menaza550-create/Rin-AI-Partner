import streamlit as st
import google.generativeai as genai
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image
import os, base64, asyncio, edge_tts, groq

# --- 1. การตั้งค่าหน้าตาแอป (White & Clean) ---
st.set_page_config(page_title="Rin Secretary v35.1", layout="centered")

st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 21px !important; }
    
    /* ปุ่มเมนูวงกลมสีม่วงขนาดใหญ่ */
    button[data-testid="stSidebarCollapse"] {
        background-color: #DDA0DD !important;
        color: white !important;
        border-radius: 50% !important;
        width: 60px !important;
        height: 60px !important;
        position: fixed !important;
        top: 15px !important;
        left: 15px !important;
        box-shadow: 0 4px 15px rgba(221, 160, 221, 0.5) !important;
        z-index: 1000 !important;
        border: 2px solid #ffffff !important;
    }
    button[data-testid="stSidebarCollapse"] svg { width: 35px !important; height: 35px !important; fill: white !important; }
    
    .stChatMessage { background-color: #f8f9fa !important; border: 1px solid #e0e0e0 !important; border-radius: 12px; }
    header, #MainMenu, footer { visibility: visible !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 🛠️ 2. จุดที่แก้ไข: ระบบเช็กกุญแจ GOOGLE_API_KEY ---
try:
    # รินจะลองหยิบกุญแจ Gemini มาเปิดสมองค่ะ
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    # ถ้าหาไม่เจอ รินจะบอกบอสด้วยข้อความนี้แทนหน้าจอแดงค่ะ
    st.error("👓 บอสคะ! รินหากุญแจ GOOGLE_API_KEY ไม่เจอในหน้า Secrets ค่ะ รบกวนบอสไปใส่ให้รินหน่อยนะ คะ (ถ้าใส่แล้วอาจจะพิมพ์ชื่อผิด ลองเช็กดูอีกทีนะ คะ)")
    st.stop() # หยุดการทำงานเพื่อให้ระบบไม่พังค่ะ

# --- 3. ระบบความจำ (Google Sheets) ---
def save_to_rin_memory(detail):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Rin_Memory").worksheet("customer_data")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "บอสคิริลิ", detail])
        return True
    except: return False

# --- 4. ฟังก์ชันแสดงร่างริน & เสียง ---
def show_rin():
    path = "1000024544.mp4"
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'''<div style="display:flex;justify-content:center;margin-bottom:10px;"><video width="220" autoplay loop muted playsinline style="border-radius:15px;border:2px solid #DDA0DD;"><source src="data:video/mp4;base64,{b64}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

if "messages" not in st.session_state: st.session_state.messages = []

# --- 5. Sidebar ---
with st.sidebar:
    st.markdown("### Rin Settings 👓")
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

show_rin()
st.markdown("<h3 style='text-align:center;'>Rin Secretary v35.1</h3>", unsafe_allow_html=True)

# ส่วนอัปโหลดรูปภาพ
uploaded_file = st.file_uploader("📷 ส่งรูปภาพให้รินช่วยดูได้นะ คะบอส...", type=['jpg','jpeg','png'])
if uploaded_file:
    st.image(uploaded_file, caption="รินกำลังเพ่งมองอยู่ค่ะ...", width=300)

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 6. ส่วนรับคำสั่ง ---
col_mic, col_pad = st.columns([1, 5])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444", recording_color="#ff4b4b")

prompt = st.chat_input("คุยกับริน หรือสั่งให้ริน 'จด' ได้เลยค่ะ...")
final_input = None

if audio:
    client = groq.Groq(api_key=st.secrets["GROQ_API_KEY"])
    with open("t.wav", "wb") as f: f.write(audio)
    with open("t.wav", "rb") as f:
        final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text
elif prompt: final_input = prompt

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        if any(w in final_input for w in ["จด", "บันทึก", "จำ"]):
            if save_to_rin_memory(final_input):
                answer = "เรียบร้อยค่ะบอส! รินจดลง Sheets ให้แล้วนะ คะ 👓✨"
            else: answer = "รินจดไม่ได้ค่ะ เช็กสิทธิ์ Sheets หน่อยนะ คะ"
        else:
            with st.spinner("รินกำลังประมวลผล..."):
                tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                context = ""
                if any(w in final_input for w in ["ราคา", "ข่าว", "เช็ค"]):
                    try:
                        res = tavily.search(query=final_input, max_results=3)
                        context = "".join([r['content'] for r in res['results']])
                    except: pass
                
                # เรียกใช้สมอง Gemini
                model = genai.GenerativeModel('gemini-1.5-flash')
                content_parts = [f"คุณคือริน เลขาบอสคิริลิ ข้อมูลเน็ต: {context} ตอบหวานๆ ค่ะ/คะ"]
                
                for m in st.session_state.messages:
                    content_parts.append(f"{m['role']}: {m['content']}")
                
                if uploaded_file:
                    img = Image.open(uploaded_file)
                    content_parts.append(img)
                
                content_parts.append(f"User current input: {final_input}")
                
                response = model.generate_content(content_parts)
                answer = response.text
        
        st.markdown(answer)
        if voice_on:
            asyncio.run(make_voice(answer))
            st.audio("rin_voice.mp3", autoplay=True)
        st.session_state.messages.append({"role": "assistant", "content": answer})
