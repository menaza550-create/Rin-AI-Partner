import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64

# --- 🌑 1. CONFIG & DARK STYLE (GEMINI DARK LOOK) ---
st.set_page_config(page_title="Rin AI Assistant", layout="wide")

# CSS ปรับแต่งให้เป็น Dark Mode 100% และเปิดเมนูให้เห็นชัดเจน
st.markdown("""
    <style>
    /* พื้นหลังสีดำเข้มแบบ Gemini Dark */
    .stApp {
        background-color: #131314 !important;
    }
    
    /* ปรับแต่ง Font และสีตัวหนังสือเป็นสีขาว/เทาอ่อน */
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif;
        color: #e3e3e3 !important;
    }

    /* เปิดเมนู 3 ขีดและส่วนหัวให้เห็นเป็นสีดำ */
    header[data-testid="stHeader"] {
        background-color: #131314 !important;
        visibility: visible !important;
    }
    #MainMenu { visibility: visible !important; }

    /* ปรับแต่งกล่องแชท */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 20px 0px !important;
    }
    
    /* ปรับแต่งช่อง Input ด้านล่างให้เป็นสีเทาเข้ม */
    .stChatInputContainer {
        padding-bottom: 30px !important;
        background-color: transparent !important;
    }
    .stChatInputContainer > div {
        border-radius: 28px !important;
        border: 1px solid #444746 !important;
        background-color: #1e1f20 !important;
        color: #ffffff !important;
    }
    textarea {
        color: #ffffff !important;
    }

    /* วิดีโอ Avatar วงกลม */
    .video-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    .video-container video {
        border-radius: 50%;
        border: 2px solid #444746;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    
    /* ปรับสีไอคอนและปุ่ม */
    button p { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 🧠 2. MEMORY SYSTEM (GOOGLE SHEETS) ---
def save_to_memory(boss_input):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Rin_Memory").worksheet("customer_data")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "Boss Kirili", boss_input])
        return True
    except Exception as e:
        return f"รินจดไม่ได้ค่ะบอส: {e}"

# --- 🖼️ 3. AVATAR LOADING ---
def get_rin_avatar():
    path = "1000024544.mp4"
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            return f'data:video/mp4;base64,{b64}'
    return None

# --- 🤖 4. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงวิดีโอริน
rin_video = get_rin_avatar()
if rin_video:
    st.markdown(f'''<div class="video-container"><video width="130" height="130" autoplay loop muted playsinline><source src="{rin_video}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

# แสดงข้อความแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ช่องพิมพ์คำสั่ง
prompt = st.chat_input("รินรอรับคำสั่งอยู่ในความมืดค่ะบอส...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # ระบบจดบันทึก
        if any(k in prompt for k in ["จด", "บันทึก", "จำ"]):
            status = save_to_memory(prompt)
            response = "เรียบร้อยค่ะ! รินจดลง Sheets ให้แล้วนะ คะ 👓✨" if status is True else status
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "คุณคือริน เลขาส่วนตัวบอสคิริลิ (Piyawut) ตอบหวานๆ ค่ะ/คะ"},
                        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    ],
                )
                response = res.choices[0].message.content
            except Exception as e:
                response = f"สมองรินล้าไปนิดค่ะบอส: {e}"

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
