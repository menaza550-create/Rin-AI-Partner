import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from datetime import datetime
import os, base64, asyncio, edge_tts

# --- 1. UI & Styling (CSS สำหรับเมนู) ---
st.set_page_config(page_title="Rin v37.3 Partner", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 19px; }
    .stChatMessage { background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }
    
    /* สไตล์สำหรับเมนูลัด (Action Chips) */
    .action-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }
    .action-chip { display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; font-size: 16px !important; font-weight: bold; transition: 0.3s; text-align: center; }
    .action-chip:hover { background-color: #DDA0DD; color: #ffffff !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ML & Memory Logic (ระบบเรียนรู้) ---
def get_diana_memory():
    """ดึงความจำที่ ML เรียนรู้มาเข้าสมองริน"""
    if "lessons" not in st.session_state: return "กำลังเริ่มเรียนรู้นิสัยบอสค่ะ"
    return "\n".join(st.session_state.lessons[-5:])

def save_new_lesson(u_msg):
    """บันทึกบทเรียนใหม่ลงสมองริน"""
    if "lessons" not in st.session_state: st.session_state.lessons = []
    timestamp = datetime.now().strftime('%H:%M')
    st.session_state.lessons.append(f"[{timestamp}] บอสสนใจเรื่อง: {u_msg}")

# --- 3. Sidebar: จัดการระบบ ---
with st.sidebar:
    st.markdown("### 🧠 Diana ML Engine")
    st.success("Brain: Llama 4 Maverick 🟢")
    if st.button("🔍 ตรวจสอบ ID สมองบน Groq"):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            for m in client.models.list().data: st.code(m.id)
        except: st.error("ดึงข้อมูลไม่ได้ค่ะ")
    st.divider()
    search_mode = st.toggle("🔍 สแกนเน็ต (Web Search)", value=False)
    voice_on = st.toggle("🔊 เปิดเสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน่วยความจำ"):
        st.session_state.messages = []; st.session_state.lessons = []; st.rerun()

# --- 4. Main UI & เมนูที่หายไป (Action Menu) ---
st.markdown("<h2 style='text-align:center;'>👓 Rin v37.3 Partner</h2>", unsafe_allow_html=True)

# แถบเมนูลัดกลับมาแล้วค่ะบอส!
st.markdown('<div class="action-container">'
    '<a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a>'
    '<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>'
    '<a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>'
    '<a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>'
    '</div>', unsafe_allow_html=True)
st.write("---")

# แสดงประวัติการสนทนา
if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. Input Layer ---
prompt = st.chat_input("สั่งการริน Maverick ได้เลยค่ะบอส...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("กำลังประมวลผลและเรียนรู้บริบท..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                past_memory = get_diana_memory()
                
                # Maverick Chain (ลำดับสมองที่เลือกใช้)
                maverick_chain = ["llama-4-maverick-70b-instruct", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
                
                sys_msg = f"คุณคือ 'ริน' เวอร์ชั่น Maverick AI คู่หูบอสคิริลิ บุคลิกสุขุม ฉลาดนิ่ง ความจำปัจจุบัน: {past_memory} ลงท้าย ค่ะ/คะ เสมอ"
                
                answer = ""
                for model_id in maverick_chain:
                    try:
                        res = client.chat.completions.create(model=model_id, messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:])
                        answer = res.choices[0].message.content
                        break
                    except: continue
                
                if not answer: answer = "ขออภัยค่ะบอส ระบบขัดข้องชั่วคราว"
                
                st.markdown(answer)
                save_new_lesson(prompt) # บันทึกเพื่อเรียนรู้ด้วยตัวเอง
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # ระบบเสียง (ล่องหน)
                if voice_on:
                    communicate = edge_tts.Communicate(answer, "th-TH-PremwadeeNeural", rate="-10%", pitch="+2Hz")
                    asyncio.run(communicate.save("rin_voice.mp3"))
                    with open("rin_voice.mp3", "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                        st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {str(e)}")
