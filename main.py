import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64
from PIL import Image

# 👓 1. Setup หน้าตาแอป (White & Clean)
st.set_page_config(page_title="Rin Super Secretary", layout="centered")

# --- 🎨 CSS: ตัวหนังสือดำ อ่านง่ายสไตล์บอส ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 20px !important; }
    .stChatMessage { background-color: #f1f3f5 !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 🧠 ระบบบันทึกความจำ (Google Sheets) ---
def save_note(detail):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Rin_Memory").worksheet("customer_data")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "Boss Kirili", detail])
        return True
    except: return False

# --- ⚙️ ตั้งค่า Gemini Brain ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash') # รุ่นที่อ่านรูปเก่งและไวมากค่ะ

# --- 🖼️ ส่วนแสดงร่างเลขาริน ---
st.markdown("<h2 style='text-align: center;'>Rin v29.0 (Gemini Powered)</h2>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 📸 ส่วนรับรูปภาพ ---
uploaded_file = st.file_uploader("ส่งรูปภาพให้รินช่วยดูได้นะ คะบอส...", type=['jpg', 'jpeg', 'png'])

prompt = st.chat_input("สั่งรินจดบันทึก หรือถามคำถามได้เลยค่ะ...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินกำลังคิดคำตอบหวานๆ ให้บอสค่ะ..."):
            if "จด" in prompt or "บันทึก" in prompt:
                save_note(prompt)
                response_text = "รินจดลง Sheets ให้บอสเรียบร้อยแล้วค่ะ! 👓✨💖"
            else:
                # ถ้ามีการส่งรูปภาพมาด้วย
                if uploaded_file:
                    img = Image.open(uploaded_file)
                    res = model.generate_content([f"คุณคือริน เลขาสาวแว่นที่อ่อนหวานของบอสคิริลิ ตอบเป็นภาษาไทยหวานๆ: {prompt}", img])
                else:
                    res = model.generate_content(f"คุณคือริน เลขาสาวแว่นที่อ่อนหวานของบอสคิริลิ ตอบเป็นภาษาไทยหวานๆ: {prompt}")
                
                response_text = res.text
            
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text}) "content": answer})
