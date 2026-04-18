import streamlit as st
from groq import Groq
import os
import base64

# --- 1. หน้าตาแอปแบบมาตรฐาน (เห็นเมนูครบถ้วน) ---
st.set_page_config(page_title="Rin AI Assistant v27.0", layout="centered")

# CSS แบบคลีน: พื้นหลังขาว ตัวหนังสือดำ เมนูอยู่ครบ
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    * { color: #000000 !important; font-size: 20px; }
    .stChatInputContainer { background-color: #f0f2f6; }
    /* เปิดให้เห็นเมนู 3 ขีดและทุกอย่างตามปกติ */
    #MainMenu, header, footer { visibility: visible !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันแสดงน้องริน (1000024544.mp4) ---
def display_rin():
    video_path = "1000024544.mp4"
    if os.path.exists(video_path):
        with open(video_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
        st.markdown(f'''
            <div style="text-align: center; margin-bottom: 20px;">
                <video width="280" autoplay loop muted playsinline style="border-radius: 20px; border: 2px solid #ffccff;">
                    <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                </video>
            </div>
        ''', unsafe_allow_html=True)

# --- 3. ส่วนหัวข้อและประวัติแแชท ---
display_rin()
st.markdown("<h2 style='text-align: center;'>Rin Secretary v27.0</h2>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. การประมวลผลคำสั่ง ---
prompt = st.chat_input("คุยกับรินได้เลยค่ะบอส...")

if prompt:
    # แสดงข้อความบอส
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # รินตอบกลับ
    with st.chat_message("assistant", avatar="👓"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "คุณคือริน (Rin) เลขาส่วนตัวของบอสคิริลิ ใส่แว่น หูแมว ตอบหวานๆ ลงท้าย ค่ะ/คะ เสมอ"},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                ],
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"รินขอโทษค่ะบอส สมองรินขัดข้องนิดหน่อย: {e}"
        
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
