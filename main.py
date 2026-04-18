import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64

# --- 🌑 1. CONFIG & DARK STYLE (HIGH VISIBILITY) ---
st.set_page_config(page_title="Rin AI Assistant", layout="wide")

st.markdown("""
    <style>
    /* 1. พื้นหลังดำสนิทแบบพรีเมียม */
    .stApp {
        background-color: #0e0e10 !important;
    }
    
    /* 2. บังคับให้ไอคอนเมนู (3 ขีด) และ Header แสดงผลเป็นสีสว่าง */
    header[data-testid="stHeader"] {
        background-color: rgba(14, 14, 16, 0.8) !important;
        visibility: visible !important;
        color: white !important;
    }
    
    /* ทำให้ปุ่มเมนู 3 ขีดเห็นชัดขึ้น */
    button[kind="header"] {
        color: white !important;
    }

    /* 3. ปรับแต่ง Font และสีตัวหนังสือ */
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif;
        color: #efefef !important;
    }

    /* 4. ปรับแต่งกล่องแชท */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 15px 0px !important;
    }
    
    /* 5. ช่องพิมพ์คำสั่ง (Gemini Style) */
    .stChatInputContainer {
        padding-bottom: 30px !important;
        background-color: transparent !important;
    }
    .stChatInputContainer > div {
        border-radius: 30px !important;
        border: 1px solid #3c4043 !important;
        background-color: #1e1f20 !important;
    }
    textarea {
        color: #ffffff !important;
    }

    /* 6. วิดีโอ Avatar วงกลม */
    .video-container {
        display: flex;
        justify-content: center;
        margin-bottom: 25px;
        margin-top: 10px;
    }
    .video-container video {
        border-radius: 50%;
        border: 2px solid #3c4043;
        box-shadow: 0 8px 32px rgba(0,0,0,0.8);
    }
    
    /* ซ่อน Footer ของ Streamlit แต่เปิดเมนูไว้ */
    footer { visibility: hidden; }
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
        # บันทึก วันที่ | บอสคิริลิ | ข้อความ
        sheet.append_row([now, "Boss Kirili", boss_input])
        return True
    except Exception as e:
        return f"รินบันทึกไม่ได้ค่ะ: {e}"

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

# แสดงวิดีโอรินสบตาบอส
rin_video = get_rin_avatar()
if rin_video:
    st.markdown(f'''<div class="video-container"><video width="140" height="140" autoplay loop muted playsinline><source src="{rin_video}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

# แสดงประวัติการแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ช่องรับคำสั่ง
prompt = st.chat_input("รินรอรับคำสั่งอยู่ในโหมด Dark ค่ะบอส...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # ระบบวิเคราะห์คำสั่ง (จดบันทึก)
        if any(k in prompt for k in ["จด", "บันทึก", "จำ"]):
            status = save_to_memory(prompt)
            response = "เรียบร้อยค่ะ! รินจดลง Sheets ให้บอสแล้วนะคะ 👓✨" if status is True else status
        else:
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "คุณคือริน (Rin) เลขาของบอสคิริลิ ตอบหวานๆ ค่ะ/คะ เสมอ"},
                        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    ],
                )
                response = res.choices[0].message.content
            except Exception as e:
                response = f"สมองรินล้านิดหน่อยค่ะบอส: {e}"

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
