import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import os
import base64
import asyncio
import edge_tts

# 👓 1. Setup หน้าตาแอป (เน้นความชัดเจนสูงสุด)
st.set_page_config(page_title="Rin :: Private Secretary", layout="centered")

# --- 🎨 CSS: ดำสนิท ตัวขาวใหญ่ (24px) แยกสีแชทชัดเจน ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    
    /* กล่องแชท: พื้นดำสนิท ตัวหนังสือสีขาวบริสุทธิ์ */
    .stChatMessage { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        border: 2px solid #333 !important;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .stChatMessage p, .stChatMessage div, .stChatMessage span {
        font-size: 24px !important; /* ขยายใหญ่พิเศษตามสั่งค่ะ */
        color: #ffffff !important;
        font-weight: 500;
    }
    
    /* ช่อง Input และ Sidebar */
    .stTextInput input { border-radius: 30px !important; background-color: #111 !important; color: white !important; font-size: 20px !important; }
    [data-testid="stSidebar"] { background-color: #0a0a0a; border-right: 1px solid #222; }
    </style>
    """, unsafe_allow_html=True)

# --- 🎭 ฟังก์ชันแสดงวิดีโอ (แยกโหมดเด็ดขาด) ---
def render_rin_frame(mood, is_live):
    # ❌ โหมดปกติ: บังคับใช้รูป/วิดีโอ 1000024544 เท่านั้น
    if not is_live:
        target_file = "1000024544"
    else:
        # ✨ โหมด Live: สลับตามอารมณ์
        file_map = {"normal": "normal", "wave": "wave", "shy": "shy"}
        target_file = file_map.get(mood, "normal")
    
    for ext in [".mp4", ".MP4", ".mov"]:
        path = target_file + ext
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
            return f'''
                <div style="display: flex; justify-content: center; margin-bottom: 25px;">
                    <video width="340" autoplay loop muted playsinline style="border-radius: 50%; border: 5px solid #DDA0DD; box-shadow: 0 0 25px #DDA0DD;">
                        <source src="data:video/mp4;base64,{b64}" type="video/mp4">
                    </video>
                </div>'''
    return "<p style='text-align:center; color:red;'>บอสคะ รินหาไฟล์วิดีโอไม่เจอค่ะ!</p>"

# --- 🔊 เสียงหวานพรีเมียม ---
async def generate_voice(text):
    VOICE = "th-TH-PremwadeeNeural"
    communicate = edge_tts.Communicate(text, VOICE, rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

# --- 🧠 ระบบจัดการอารมณ์ ---
def get_mood(text):
    t = text.lower()
    if any(w in t for w in ["สวัสดี", "ทักทาย", "ยินดี", "โบกมือ"]): return "wave"
    if any(w in t for w in ["รัก", "ชอบ", "สวย", "เขิน", "จูบ"]): return "shy"
    return "normal"

# --- 💾 ระบบความจำ ---
if "messages" not in st.session_state: st.session_state.messages = []
if "mood" not in st.session_state: st.session_state.mood = "normal"

# --- 🛠️ Sidebar: ปุ่มแยกโหมดเด็ดขาด ---
with st.sidebar:
    st.title("Rin Control Center 👓")
    mode_selection = st.selectbox("โหมดการทำงาน:", ["💬 แชทปกติ (รูป 1000024544)", "✨ โหมด Live (ขยับร่าง)"])
    is_live = "Live" in mode_selection
    
    st.write("---")
    think_lvl = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างประวัติแชท"):
        st.session_state.messages = []
        st.session_state.mood = "normal"
        st.rerun()

# --- แสดงร่างริน ---
st.markdown(render_rin_frame(st.session_state.mood, is_live), unsafe_allow_html=True)

# --- แสดงประวัติแชท ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- ส่วนรับคำสั่ง ---
col_mic, col_in = st.columns([1, 5])
with col_mic:
    audio = audio_recorder(text="", icon_size="2x", neutral_color="#444")

prompt = st.chat_input("คุยกับเลขารินได้เลยค่ะบอส...")

final_input = None
if audio:
    with st.spinner("รินกำลังฟังเสียงบอส..."):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "wb") as f: f.write(audio)
        with open("t.wav", "rb") as f:
            final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text
elif prompt:
    final_input = prompt

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินกำลังประมวลผล..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
            
            # ค้นหาข้อมูลถ้าจำเป็น
            context = ""
            if "Max" in think_lvl or any(w in final_input for w in ["เช็ค", "ราคา", "ข่าว"]):
                search = tavily.search(query=final_input, search_depth="basic", max_results=3)
                context = "".join([r['content'] for r in search['results']])

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"คุณคือริน เลขาบอสคิริลิ ข้อมูลคือ: {context} ตอบหวานๆ ลงท้าย 'ค่ะ/คะ'"},
                          *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]]
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            
            # อัปเดตอารมณ์และเสียง
            new_mood = get_mood(answer)
            asyncio.run(generate_voice(answer))
            if voice_on: st.audio("rin_voice.mp3", autoplay=True)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # 🛡️ Rerun Guard: จะโหลดใหม่เฉพาะตอนโหมด Live เปลี่ยนท่าทางเท่านั้น
            if is_live and new_mood != st.session_state.mood:
                st.session_state.mood = new_mood
                st.rerun()
            elif not is_live:
                st.session_state.mood = "normal" # โหมดปกติห้ามเปลี่ยนร่างค่ะ
