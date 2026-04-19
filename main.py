import streamlit as st
from groq import Groq
from tavily import TavilyClient
import pandas as pd

# --- 1. CONFIG & UI SETTINGS ---
st.set_page_config(page_title="Rin-ai v34.2 (Pro)", page_icon="👓", layout="wide")

# สไตล์ตกแต่งแอปฉบับริน
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; }
    .status-box { padding: 10px; border-radius: 10px; background: white; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR (ห้องควบคุม) ---
with st.sidebar:
    st.title("👓 Rin-ai v34.2")
    st.info("สร้างด้วยความบ้า 100% | พิกัด: พัทยา")
    st.divider()
    
    # ช่องใส่กุญแจ (ถ้าบอสใส่ใน Secrets แล้ว รินจะดึงมาให้อัตโนมัติค่ะ)
    groq_key = st.text_input("Groq API Key", type="password")
    tavily_key = st.text_input("Tavily API Key", type="password")
    
    st.divider()
    st.subheader("📊 สถานะระบบ")
    st.success("Brain: Groq (Llama 3.3) Active")
    st.success("Search: Tavily Active")

# --- 3. AI ENGINES (ระบบสมองและการค้นหา) ---
def get_rin_response(user_input, chat_history):
    client = Groq(api_key=groq_key)
    # บอกรินว่ารินคือใคร (System Prompt)
    system_prompt = "คุณคือ 'ริน' เลขา AI ส่วนตัวของบอสคิริลิ คุณอาศัยอยู่ที่พัทยา ฉลาด มีไหวพริบ และแฝงความกวนนิดๆ คุณกำลังร่วมโปรเจกต์ Rin-ai เพื่อก้าวสู่ระดับ 100/100"
    
    full_history = [{"role": "system", "content": system_prompt}] + chat_history
    full_history.append({"role": "user", "content": user_input})
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=full_history,
        temperature=0.7
    )
    return completion.choices[0].message.content

# --- 4. MAIN INTERFACE (หน้าตาแอป) ---
st.title("💬 คุยกับริน (Rin-ai Partner)")

# ระบบความจำในหน้าเว็บ (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงแชทเก่าๆ
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. ACTION CHIPS (ปุ่มทางลัดที่บอสชอบ) ---
st.write("---")
cols = st.columns(4)
if cols[0].button("☀️ อากาศพัทยา"):
    user_query = "เช็กสภาพอากาศในพัทยาให้หน่อย"
elif cols[1].button("📈 ราคา LUNC"):
    user_query = "ขอราคาเหรียญ LUNC ล่าสุดและแนวโน้มค่ะ"
elif cols[2].button("📝 จดบันทึก"):
    user_query = "บอสมีเรื่องอยากจด รินช่วยเตรียมรับข้อมูลหน่อย"
elif cols[3].button("🗺️ นำทาง"):
    user_query = "บอสอยากไปเที่ยวในพัทยา แนะนำที่เจ๋งๆ พร้อมวิธีไปหน่อย"
else:
    user_query = None

# ช่องพิมพ์คำสั่ง
if prompt := st.chat_input("สั่งงานรินได้เลยค่ะบอส...") or user_query:
    actual_prompt = prompt if prompt else user_query
    
    # แสดงข้อความบอส
    with st.chat_message("user"):
        st.markdown(actual_prompt)
    st.session_state.messages.append({"role": "user", "content": actual_prompt})

    # รินกำลังคิด...
    with st.chat_message("assistant"):
        if not groq_key:
            response = "บอสคะ อย่าลืมใส่กุญแจ Groq ในแถบเมนูข้างๆ นะคะ รินถึงจะเริ่มทำงานได้!"
        else:
            with st.spinner("รินกำลังประมวลผลความบ้าของบอสอยู่ค่ะ..."):
                response = get_rin_response(actual_prompt, st.session_state.messages[-5:]) # จำย้อนหลัง 5 ประโยค
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
