import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64

# --- 👓 1. Setup หน้าตาแอป (White & Clean) ---
st.set_page_config(page_title="Rin Secretary", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 22px !important; }
    .stChatMessage { background-color: #f8f9fa !important; border: 1px solid #eee !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 🧠 2. ฟังก์ชันบันทึกความจำลง Google Sheets ---
def save_to_rin_memory(detail):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # ดึงกุญแจจาก Secrets ที่บอสวางไว้
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Rin_Memory").worksheet("customer_data")
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "Boss Kirili", detail])
        return True
    except Exception as e:
        st.error(f"รินจดไม่ได้ค่ะ: {e}")
        return False

# --- 🖼️ 3. แสดงร่างริน (เลขาของบอส) ---
path = "1000024544.mp4"
if os.path.exists(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(f'''<div style="text-align:center;"><video width="250" autoplay loop muted playsinline style="border-radius:15px;"><source src="data:video/mp4;base64,{b64}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center;'>Rin Secretary v28.0</h3>", unsafe_allow_html=True)

# --- 💬 4. ส่วนแชทโต้ตอบ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("สั่งให้ริน 'จด' อะไรดีคะบอส?")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        if "จด" in prompt or "บันทึก" in prompt:
            if save_to_rin_memory(prompt):
                response_text = "เรียบร้อยค่ะบอส! รินจดบันทึกเรื่องนี้ลง Google Sheets ให้แล้วนะคะ 👓✨💖"
            else:
                response_text = "รินจดไม่ได้ค่ะ บอสแชร์สิทธิ์ใน Sheets ให้รินหรือยังคะ?"
        else:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "คุณคือริน เลขาบอสคิริลิ ตอบหวานๆ เสมอ"},
                          *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]]
            )
            response_text = res.choices[0].message.content
        
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
