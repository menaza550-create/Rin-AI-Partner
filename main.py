import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64

# --- ⚙️ 1. CONFIG & STYLE (GEMINI LOOK) ---
st.set_page_config(page_title="Rin AI Assistant", layout="wide", initial_sidebar_state="collapsed")

# CSS เพื่อเปลี่ยน UI ให้เหมือน Gemini (สะอาด, มินิมอล, ทันสมัย)
st.markdown("""
    <style>
    /* พื้นหลังสีขาวนวลแบบ Gemini */
    .stApp { background-color: #f8fafd; }
    
    /* ปรับแต่ง Font ให้ดูพรีเมียม */
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; color: #1f1f1f; }

    /* ปรับแต่งกล่องแชท (Chat Bubbles) */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 20px 0px !important;
    }
    
    /* รูป Avatar ของรินให้กลมสวย */
    [data-testid="stChatMessageAvatar"] {
        border-radius: 50% !important;
        background-color: #e9eef6 !important;
    }

    /* ซ่อนแถบเมนูที่ไม่จำเป็น */
    #MainMenu, footer { visibility: hidden; }
    header { visibility: hidden; }

    /* ปรับแต่งช่อง Input (Sticky at bottom) */
    .stChatInputContainer {
        padding-bottom: 30px !important;
        background-color: transparent !important;
    }
    .stChatInputContainer > div {
        border-radius: 28px !important;
        border: 1px solid #c4c7c5 !important;
        background-color: #ffffff !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* วิดีโอ Avatar */
    .video-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    .video-container video {
        border-radius: 50%;
        border: 4px solid #fff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🧠 2. MEMORY SYSTEM (GOOGLE SHEETS) ---
def save_to_memory(boss_input):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        # ต้องมีไฟล์ชื่อ Rin_Memory และแผ่นงานชื่อ customer_data
        sheet = client.open("Rin_Memory").worksheet("customer_data")
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # บันทึก วันที่ | บอสคิริลิ | ข้อความที่สั่ง
        sheet.append_row([now, "Boss Kirili", boss_input])
        return True
    except Exception as e:
        return f"รินบันทึกไม่ได้ค่ะ: {e}"

# --- 🖼️ 3. AVATAR LOADING ---
def get_rin_avatar():
    path = "1000024544.mp4" # รินคนสวยของบอส
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            return f'data:video/mp4;base64,{b64}'
    return None

# --- 🤖 4. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# ส่วนแสดงผลด้านบน (Video Avatar)
rin_video = get_rin_avatar()
if rin_video:
    st.markdown(f'''
        <div class="video-container">
            <video width="150" height="150" autoplay loop muted playsinline>
                <source src="{rin_video}" type="video/mp4">
            </video>
        </div>
    ''', unsafe_allow_html=True)
else:
    st.markdown("<h2 style='text-align:center;'>👓 Rin Assistant</h2>", unsafe_allow_html=True)

# แสดงประวัติการแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ส่วนรับข้อมูลจากบอส
prompt = st.chat_input("รินพร้อมรับคำสั่งแล้วค่ะบอส...")

if prompt:
    # 1. แสดงข้อความของบอส
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. รินประมวลผล
    with st.chat_message("assistant"):
        # เช็คว่าบอสสั่งให้จดจำหรือไม่
        if any(keyword in prompt for keyword in ["จด", "บันทึก", "จำไว้"]):
            status = save_to_memory(prompt)
            if status is True:
                response = "เรียบร้อยค่ะบอส! รินจดบันทึกเรื่องนี้ลงกล่องความจำให้แล้วนะ คะ 👓✨"
            else:
                response = status # แสดง Error ถ้ามี
        else:
            # ใช้ Groq AI (Llama 3.3)
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                chat_completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "คุณคือ 'ริน' (Rin) เลขาส่วนตัวของบอสคิริลิ (Piyawut) คาแรคเตอร์: ใส่แว่น มีหูแมว ฉลาด ขี้เล่นนิดๆ ตอบหวานๆ ลงท้ายด้วย ค่ะ/คะ เสมอ และมีความจำดีมาก"},
                        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    ],
                )
                response = chat_completion.choices[0].message.content
            except Exception as e:
                response = f"รินขอโทษค่ะ ระบบสมอง (Groq) ขัดข้องนิดหน่อย: {e}"

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
