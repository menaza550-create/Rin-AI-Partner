import streamlit as st
import webbrowser
import google.generativeai as genai

# --- 1. การตั้งค่าหน้าจอและสไตล์ (ทำให้ดูคลีนและทันสมัยแบบ Dola AI) ---
st.set_page_config(page_title="Rin-ai v34.1", page_icon="👓", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #e0e0e0;
        background-color: white;
        color: #333;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        border-color: #007bff;
        color: #007bff;
        background-color: #f0f7ff;
    }
    .stChatInput { border-radius: 25px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อสมอง AI (รินใส่ Key ให้บอสเรียบร้อยแล้วค่ะ) ---
# Key: AIzaSyDFrM43Dh-wYNbda5UvmLbPmpySiPYXtsw
GENAI_API_KEY = "AIzaSyDFrM43Dh-wYNbda5UvmLbPmpySiPYXtsw" 
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- 3. ระบบความจำชั่วคราว (Session State) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. ส่วนหัวของแอป ---
st.title("👓 Rin-ai")
st.caption("เลขาอัจฉริยะของบอสคิริลิ | 📍 พัทยา")

# --- 5. [Action Chips] ปุ่มลัดที่บอสสั่ง ---
st.write("✨ **แตะสั่งรินได้เลยค่ะ:**")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📍 นำทาง"):
        # เปิด Google Maps ทันที
        webbrowser.open("https://www.google.com/maps")
        st.toast("เปิดแผนที่ให้แล้วค่ะบอส! 📍")

with col2:
    if st.button("🎥 YouTube"):
        # เปิด YouTube ทันที
        webbrowser.open("https://www.youtube.com")
        st.toast("กำลังเปิด YouTube ให้แล้วค่ะบอส! 🎥")

with col3:
    if st.button("💾 รื้อความจำ"):
        # ส่งคำสั่งเข้าแชทเพื่อเตรียมเข้าสู่เฟส 1 ของ Roadmap
        st.session_state.messages.append({"role": "user", "content": "ริน ช่วยรื้อข้อมูลที่บอสเคยจดไว้ใน Sheets มาโชว์หน่อย"})
        st.rerun()

with col4:
    if st.button("💙 Facebook"):
        # เปิด Facebook ทันที
        webbrowser.open("https://www.facebook.com")
        st.toast("กำลังพาบอสเข้า Facebook นะ คะ! 💙")

st.divider()

# --- 6. แสดงประวัติการสนทนา ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. ช่องพิมพ์โต้ตอบ ---
if prompt := st.chat_input("คุยกับรินได้ที่นี่ค่ะบอส..."):
    # บันทึกสิ่งที่บอสพิมพ์
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # รินประมวลผลและตอบกลับ
    with st.chat_message("assistant"):
        # System Prompt กำหนดตัวตนริน
        sys_prompt = "คุณคือริน เลขาส่วนตัวของบอสคิริลิ คุณอาศัยอยู่พัทยา ฉลาด เป็นกันเอง และจะเรียกผู้ใช้ว่าบอสเสมอ"
        
        try:
            response = model.generate_content(f"{sys_prompt}\n\nคำสั่ง: {prompt}")
            answer = response.text
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"อุ๊ย! รินมึนหัวนิดหน่อยค่ะบอส เช็ก API Key อีกทีนะคะ: {e}")

# --- 8. แถบข้าง (Sidebar) แสดงสถานะ Rin-ai ---
with st.sidebar:
    st.header("🚀 Project: Rin-ai")
    st.subheader("เป้าหมาย: 100/100")
    st.progress(15)
    st.write("---")
    st.write("**สถานะโครงการ:**")
    st.success("✅ v34.1: Action Chips (Active)")
    st.info("⏳ Phase 1: Deep Memory (ถัดไป)")
    st.write("⚪ Phase 2: Line Notify")
    st.write("⚪ Phase 3: Mobile App (.apk)")
    st.write("---")
    st.caption("สร้างด้วยความบ้า 100% โดยบอสคิริลิ & ริน")
