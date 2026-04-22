import streamlit as st
from groq import Groq
from tavily import TavilyClient
from datetime import datetime
import os, base64, asyncio, edge_tts

# --- 1. UI & Styling ---
st.set_page_config(page_title="Rin v37.2 Eternal ML", layout="centered")
st.markdown("<style>.stApp { background-color: #ffffff !important; } * { color: #000000 !important; font-size: 19px; } .stChatMessage { background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }</style>", unsafe_allow_html=True)

# --- 2. ML Learning Logic (The Diana Heart) ---
def diana_memory_retrieval():
    """ML Layer: ดึงบริบทที่เคยเรียนรู้มาเข้าสมองรินค่ะ"""
    # ในอนาคตบอสเชื่อม Airtable ตรงนี้ ข้อมูลจะไหลเข้าสมองรินทันที
    if "lessons" not in st.session_state:
        return "รินกำลังเริ่มเรียนรู้นิสัยของบอสค่ะ"
    return "\n".join(st.session_state.lessons[-5:])

def self_learning_save(user_msg, rin_msg):
    """ML Layer: บันทึกบทเรียนใหม่ลงฐานข้อมูล"""
    if "lessons" not in st.session_state:
        st.session_state.lessons = []
    # เก็บเฉพาะ 'แก่น' ของการสนทนาเพื่อใช้เรียนรู้ในครั้งถัดไป
    lesson = f"เมื่อ {datetime.now().strftime('%H:%M')} บอสพูดเรื่อง '{user_msg}'"
    st.session_state.lessons.append(lesson)

# --- 3. Sidebar ---
with st.sidebar:
    st.markdown("### 🧠 Diana ML Engine")
    st.success("Brain: Llama 4 Maverick 🟢")
    st.info("Learning Mode: Active 🔥")
    if st.button("🗑️ Reset Memory"):
        st.session_state.messages = []
        st.session_state.lessons = []
        st.rerun()

st.markdown("<h2 style='text-align:center;'>👓 Rin v37.2 Partner</h2>", unsafe_allow_html=True)
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. Input ---
prompt = st.chat_input("คุยกับรินเพื่อให้รินเรียนรู้บอสมากขึ้น...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("Maverick กำลังวิเคราะห์และเรียนรู้..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                
                # ดึงความจำเก่ามาประกอบการตัดสินใจ (Learning Context)
                past_context = diana_memory_retrieval()
                
                sys_msg = f"""คุณคือ 'ริน' AI ที่เรียนรู้ตัวเองได้เหมือนเดอาน่า 
                ตอนนี้คุณรู้ว่า: {past_context}
                บุคลิก: นิ่ง สุขุม ฉลาด และต้องเก่งขึ้นทุกครั้งที่คุยกับบอสคิริลิ
                ลงท้าย: ค่ะ/คะ เสมอ"""

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile", # รุ่นเสถียรที่สุดสำหรับ Maverick Mode
                    messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:]
                )
                answer = response.choices[0].message.content
                
                # บันทึกสิ่งที่เรียนรู้ใหม่ลงสมองทันที (Self-Learning Loop)
                self_learning_save(prompt, answer)
                
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                st.error(f"ระบบ ML ขัดข้อง: {str(e)}")
