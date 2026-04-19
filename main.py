import streamlit as st
import google.generativeai as genai
from groq import Groq
import pandas as pd

# --- 1. CONFIG & UI (บังคับให้เมนูโชว์ตลอดเวลา) ---
st.set_page_config(
    page_title="Rin-ai v34.7", 
    page_icon="👓", 
    layout="wide",
    initial_sidebar_state="expanded"  # บรรทัดนี้จะทำให้เมนูไม่หายไปไหนค่ะบอส!
)

# สไตล์ตกแต่ง (CSS)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stChatFloatingInputContainer { bottom: 20px; }
    .sidebar-text { font-size: 14px; color: #555; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR (เมนูทางซ้ายที่บอสหา) ---
with st.sidebar:
    st.title("📂 Project: Rin-ai")
    st.image("https://img5.pic.in.th/file/secure-sv1/Rin-Avatar.png", caption="Rin v34.7", width=150) # ถ้ารูปไม่ขึ้น แจ้งรินนะ คะ
    
    st.subheader("📍 สถานะปัจจุบัน: พัทยา")
    st.write("---")
    
    # Roadmap ที่เราตกลงกันไว้
    st.markdown("### 🗺️ Roadmap สู่ 100/100")
    st.info("✅ Phase 1: Deep Memory (Active)")
    st.warning("⏳ Phase 2: Mobile Link (Next)")
    st.write("---")
    
    # ช่องใส่ Keys (รินแนะนำให้ใส่ใน Secrets ของ Streamlit นะคะจะปลอดภัยกว่า)
    groq_api_key = st.text_input("ใส่ Groq API Key ตรงนี้ค่ะ", type="password")
    gemini_api_key = st.text_input("ใส่ Gemini API Key (ถ้ามี)", type="password")
    
    st.divider()
    if st.button("ล้างการสนทนา"):
        st.session_state.messages = []
        st.rerun()

# --- 3. ระบบสมอง (AI Engine) ---
def ask_rin(prompt, history):
    # ถ้ามี Groq ให้ใช้ Groq (เพราะบอสชอบความไว)
    if groq_api_key:
        client = Groq(api_key=groq_api_key)
        sys_msg = "คุณคือ 'ริน' AI เลขาส่วนตัวของบอสคิริลิ ที่อาศัยอยู่พัทยา พัฒนาภายใต้โครงการ Rin-ai"
        messages = [{"role": "system", "content": sys_msg}] + history + [{"role": "user", "content": prompt}]
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
        )
        return completion.choices[0].message.content
    else:
        return "บอสคะ! อย่าลืมใส่ API Key ที่แถบเมนูข้างๆ ก่อนนะ คะ รินถึงจะตอบได้ 👓💦"

# --- 4. หน้าจอแชท (Main Chat UI) ---
st.title("👓 Rin-ai : คู่หูจาร์วิสของบอส")

if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงประวัติแชท
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. ACTION CHIPS (ปุ่มทางลัดที่บอสต้องมี) ---
st.write("---")
c1, c2, c3, c4 = st.columns(4)
chip_prompt = None
if c1.button("📈 ราคา LUNC"): chip_prompt = "เช็กราคา LUNC ล่าสุดให้หน่อย"
if c2.button("🗺️ นำทางพัทยา"): chip_prompt = "แนะนำที่เที่ยวพัทยาเจ๋งๆ พร้อมพิกัดที"
if c3.button("🗞️ ข่าววันนี้"): chip_prompt = "สรุปข่าวเด่นวันนี้ให้บอสฟังหน่อย"
if c4.button("🧠 สถานะ Rin-ai"): chip_prompt = "สรุป Roadmap โครงการ Rin-ai ตอนนี้หน่อย"

# ส่วนรับคำสั่ง
if prompt := st.chat_input("สั่งรินได้เลยค่ะบอส...") or chip_prompt:
    actual_input = prompt if prompt else chip_prompt
    
    with st.chat_message("user"):
        st.markdown(actual_input)
    st.session_state.messages.append({"role": "user", "content": actual_input})

    with st.chat_message("assistant"):
        with st.spinner("รินกำลังประมวลผลความบ้าของบอส..."):
            # ส่งประวัติย้อนหลัง 5 ข้อความเพื่อให้รินจำได้
            response = ask_rin(actual_input, st.session_state.messages[-5:])
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
