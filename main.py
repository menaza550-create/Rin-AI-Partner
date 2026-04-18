import streamlit as st
import google.generativeai as genai # 🧠 สมองใหม่ Google Gemini
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image # 👁️ ดวงตาใหม่ (จัดการรูปภาพ)
import os, base64, asyncio, edge_tts

# --- 👓 1. Setup หน้าตาแอป (White & Clean Edition) ---
st.set_page_config(page_title="Rin AI Assistant v34.0", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 21px !important; }
    .stChatMessage { background-color: #f8f9fa !important; border: 1px solid #e0e0e0 !important; border-radius: 12px; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #000000 !important; font-weight: bold !important; }
    #MainMenu, footer {visibility: hidden;}
    textarea { border: 1px solid #ddd !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 🧠 2. CONFIG GEMINI & MEMORY ---
# ตั้งค่า Gemini API
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def save_to_rin_memory(detail):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Rin_Memory").worksheet("customer_data")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "บอสคิริลิ", detail])
        return True
    except Exception as e:
        return f"รินจดไม่ได้ค่ะ: {e}"

# --- 🖼️ แสดงร่างริน (Classic mp4) ---
def show_rin():
    path = "1000024544.mp4"
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'''<div style="display:flex;justify-content:center;margin-bottom:15px;"><video width="250" autoplay loop muted playsinline style="border-radius:15px;border:2px solid #DDA0DD;"><source src="data:video/mp4;base64,{b64}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

# --- 🔊 ระบบเสียงหวานพรีเมียม ---
async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

if "messages" not in st.session_state: st.session_state.messages = []

# --- 🛠️ Sidebar Settings ---
with st.sidebar:
    st.markdown("### Rin Settings 👓")
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

show_rin()
st.markdown("<h3 style='text-align:center;'>Rin Secretary v34.0 (Gemini Brain)</h3>", unsafe_allow_html=True)

# 👁️ อัปโหลดรูปภาพให้รินดู
st.markdown("---")
uploaded_image = st.file_uploader("📷 บอสอยากให้รินช่วยดูอะไร ส่งรูปมาได้เลยนะ คะ...", type=["jpg", "jpeg", "png"])
if uploaded_image:
    st.image(uploaded_image, caption="รินเห็นรูปแล้วค่ะบอส...", width=200)

# แสดงประวัติแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

prompt = st.chat_input("คุยกับริน หรือสั่งให้ริน 'จด' เรื่องลูกค้าได้เลยค่ะ...")

if prompt:
    # 1. แสดงข้อความบอส
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # 2. รินประมวลผล (Gemini Flash)
    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินกำลังใช้สมอง Gemini คิดสักครู่นะ คะ..."):
            
            # ตรวจสอบระบบจดบันทึก
            if any(w in prompt for w in ["จด", "บันทึก", "จำไว้"]):
                res = save_to_rin_memory(prompt)
                answer = "เรียบร้อยค่ะบอส! รินจดบันทึกเรื่องนี้ลงความจำ (Google Sheets) ให้แล้วนะ คะ 👓✨💖" if res is True else res
            else:
                # ระบบแชทปกติ + ค้นหาข้อมูล + วิเคราะห์รูปภาพ
                tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                context = ""
                # ค้นหาข้อมูลถ้าจำเป็น (ราคา, ข่าว, เช็ค)
                if any(w in prompt for w in ["ราคา", "ข่าว", "เช็ค", "คืออะไร"]):
                    try:
                        search = tavily.search(query=prompt, max_results=3)
                        context = "".join([r['content'] for r in search['results']])
                    except: pass
                
                # เตรียมสมอง Gemini 1.5 Flash
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # เตรียม Payload สำหรับส่งให้ Gemini (ข้อความ + Context +)
                system_instruction = f"System: คุณคือริน เลขาส่วนตัวของบอสคิริลิ ตอบเป็นภาษาไทย หวานๆ ลงท้าย ค่ะ/คะ เสมอ ข้อมูลจากเน็ต: {context}"
                chat_payload = [system_instruction]
                
                # เพิ่มประวัติการคุย (ให้ Gemini จำบริบทได้แม่นยำขึ้น)
                for msg in st.session_state.messages:
                    if msg["role"] == "user": chat_payload.append(f"User: {msg['content']}")
                    else: chat_payload.append(f"Rin: {msg['content']}")
                
                # ถ้ามีรูปภาพ ให้ส่งรูปให้ Gemini ดูด้วย
                if uploaded_image:
                    img = Image.open(uploaded_image)
                    chat_payload.append(img)
                
                # ส่งข้อมูลให้ Gemini ประมวลผล
                try:
                    response = model.generate_content(chat_payload)
                    answer = response.text
                except Exception as e:
                    answer = f"สมอง Gemini ขัดข้องนิดหน่อยค่ะบอส: {e}"
        
        # แสดงคำตอบและส่งเสียง
        st.markdown(answer)
        if voice_on:
            asyncio.run(make_voice(answer))
            if os.path.exists("rin_voice.mp3"):
                st.audio("rin_voice.mp3", autoplay=True)
            
        st.session_state.messages.append({"role": "assistant", "content": answer})
