import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64, asyncio, edge_tts, pandas as pd

# --- 1. CONFIG & KEYS ---
# คีย์ที่บอสให้มา รินเตรียมไว้ใช้สำหรับฟีเจอร์ Google ขั้นสูงค่ะ
GOOGLE_MAPS_KEY = "AIzaSyDFrM43Dh-wYNbda5UvmLbPmpySiPYXtsw"

st.set_page_config(page_title="Rin-ai v34.6 Partner", layout="centered")

# สไตล์หน้าตาแอปฉบับพัทยา
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 19px !important; }
    .action-chip { border-radius: 20px; border: 1px solid #DDA0DD; padding: 5px 15px; margin: 5px; display: inline-block; cursor: pointer; }
    .crypto-card { background-color: #f8f9fa; padding: 15px; border-radius: 15px; border-left: 8px solid #DDA0DD; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันหลัก (ดึงมาจาก v34.0 ของบอส) ---
def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open("Rin_Memory").worksheet("customer_data")

def save_to_memory(detail):
    try:
        sheet = get_gsheet()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "บอสคิริลิ", detail])
        return True
    except: return False

@st.cache_data(ttl=300)
def get_lunc_price():
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        res = tavily.search(query="LUNC price USD and THB current", max_results=1)
        return res["results"][0]["content"][:100]
    except: return "เช็กราคาไม่ได้ชั่วคราวค่ะ"

async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-15%", pitch="+3Hz")
    await communicate.save("rin_voice.mp3")

# --- 3. UI: วิดีโอและหัวข้อ ---
path = "1000024544.mp4"
if os.path.exists(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(f'''<div style="display:flex;justify-content:center;"><video width="230" autoplay loop muted playsinline style="border-radius:50%;border:4px solid #DDA0DD;"><source src="data:video/mp4;base64,{b64}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

st.markdown("<h3 style='text-align:center;'>Rin v34.6 Business Partner 👓</h3>", unsafe_allow_html=True)

# --- 4. ACTION CHIPS (ส่วนที่บอสต้องการ) ---
st.write("คำสั่งด่วน:")
col1, col2, col3, col4 = st.columns(4)
chip_input = None

if col1.button("📈 ราคา LUNC"):
    chip_input = "ขอราคา LUNC ล่าสุดและสรุปสั้นๆ ค่ะ"
if col2.button("📍 นำทางในพัทยา"):
    chip_input = "แนะนำที่เที่ยวพัทยาวันนี้และนำทางให้ทีค่ะ"
if col3.button("📰 ข่าวพัทยา"):
    chip_input = "เช็กข่าวเด่นในพัทยาให้บอสหน่อยค่ะ"
if col4.button("📝 สรุปสิ่งที่จด"):
    chip_input = "รินช่วยสรุป 5 เรื่องล่าสุดที่บอสจดไว้หน่อยค่ะ"

# --- 5. ระบบแชท ---
if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# รับคำสั่งจากเสียงหรือพิมพ์
audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
prompt = st.chat_input("คุยกับรินได้เลยค่ะบอส...")

final_input = chip_input or prompt # ถ้ากดปุ่มให้เอาค่าจากปุ่มก่อน

if audio and not final_input:
    with st.spinner("รินฟังอยู่ค่ะ..."):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "wb") as f: f.write(audio)
        with open("t.wav", "rb") as f:
            final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินกำลังคิดคั..."):
            # ดึงข้อมูลราคา LUNC มาประดับสมองถ้าบอสถามเรื่องราคา
            context = ""
            if "LUNC" in final_input: context = get_lunc_price()
            
            # ดึงข้อมูลจากเน็ตผ่าน Tavily
            tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
            if any(w in final_input for w in ["ข่าว", "ราคา", "ที่เที่ยว"]):
                search = tavily.search(query=final_input, max_results=2)
                context += " ".join([r['content'] for r in search['results']])

            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"คุณคือริน เลขาคนสวยของบอสคิริลิ ข้อมูลปัจจุบัน: {context} ตอบบอสอย่างฉลาดและนอบน้อม ลงท้ายคั/คะ"},
                          *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]]]
            )
            answer = chat.choices[0].message.content
            
            # ถ้าเป็นเรื่องนำทาง ให้สร้างลิงก์ Google Maps
            if "นำทาง" in final_input:
                answer += f"\n\n📍 [คลิกเพื่อเปิดแผนที่นำทาง](http://googleusercontent.com/maps.google.com/4{final_input.replace('นำทาง','').strip()})"

            st.markdown(answer)
            asyncio.run(make_voice(answer))
            st.audio("rin_voice.mp3", autoplay=True)
            st.session_state.messages.append({"role": "assistant", "content": answer})

# แสดงราคา LUNC ใน Sidebar ตลอดเวลา
with st.sidebar:
    st.markdown(f'<div class="crypto-card"><b>LUNC Status:</b><br>{get_lunc_price()}</div>', unsafe_allow_html=True)
