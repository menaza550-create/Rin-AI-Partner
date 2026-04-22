import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from datetime import datetime
import os, base64, asyncio, edge_tts

# --- 1. UI & Styling ---
st.set_page_config(page_title="Rin v36.8 Dual-Brain", layout="centered")
st.markdown("<style>.stApp { background-color: #ffffff !important; } * { color: #000000 !important; font-size: 19px; } .stChatMessage { background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; } .crypto-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #DDA0DD; margin-bottom: 15px;}</style>", unsafe_allow_html=True)

# --- 2. Core Systems ---
def play_audio_hidden(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{base64.b64encode(f.read()).decode()}" type="audio/mp3"></audio>', unsafe_allow_html=True)

async def make_voice(text):
    # ปรับจังหวะเสียงตามสมองที่ใช้
    rate = "-8%" if st.session_state.get('brain_mode') == "Power" else "-12%"
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate=rate, pitch="+2Hz")
    await communicate.save("rin_voice.mp3")

# --- 3. Sidebar: ระบบสลับโหมดสมอง ---
with st.sidebar:
    st.markdown("### 🧠 Brain Control Center")
    brain_choice = st.select_slider(
        "เลือกโหมดสมองของริน:",
        options=["Speed", "Auto", "Power"],
        value="Auto",
        help="Speed: Llama 4 Scout | Power: Llama 4 Behemoth"
    )
    st.session_state.brain_mode = brain_choice
    
    status_color = "🔴" if brain_choice == "Power" else "⚡" if brain_choice == "Speed" else "🤖"
    st.info(f"Mode: {brain_choice} {status_color}")
    
    st.divider()
    search_mode = st.toggle("🔍 สแกนเน็ต (Web Search)", value=False)
    voice_on = st.toggle("🔊 เปิดเสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน่วยความจำ"): st.session_state.messages = []; st.rerun()

st.markdown("<h2 style='text-align:center;'>👓 Rin v36.8 Partner</h2>", unsafe_allow_html=True)

# --- 4. Chat Interface ---
if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
prompt = st.chat_input("คุยกับรินได้เลยค่ะบอส...")

final_input = None
if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            final_input = ts.text
    except: st.error("ระบบรับเสียงขัดข้อง")
elif prompt: final_input = prompt

# --- 5. Brain Processing (Dual-Brain Logic) ---
if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner(f"รินกำลังประมวลผลในโหมด {brain_choice}..."):
            # กำหนด ID โมเดล
            BEHEMOTH = "llama-4-behemoth-405b-instruct"
            SCOUT = "llama-4-scout-17b-16e-instruct"
            SAFE = "llama-3.3-70b-versatile"

            # เลือกโมเดลหลักตามที่บอสตั้งค่า
            if brain_choice == "Power": primary = BEHEMOTH
            elif brain_choice == "Speed": primary = SCOUT
            else: primary = BEHEMOTH # Auto เริ่มที่ตัวใหญ่ก่อน

            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                search_ctx = ""
                if search_mode:
                    try:
                        res = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"]).search(query=final_input, max_results=2)
                        search_ctx = "\n[Web ข้อมูล]: " + " ".join([r['content'] for r in res['results']])
                    except: pass

                sys_msg = f"คุณคือ 'ริน' เวอร์ชั่น {brain_choice} ดูแลบอสคิริลิ บุคลิกนิ่ง สุขุม ฉลาด ลงท้าย ค่ะ/คะ เสมอ {search_ctx}"
                
                # พยายามใช้โมเดลหลัก
                response = client.chat.completions.create(model=primary, messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:])
                answer = response.choices[0].message.content

            except Exception as e:
                # 🛡️ Fallback Logic: ถ้าตัวหลักพังหรือคิวยาว ให้สลับไปตัวสำรองทันที
                fallback_model = SCOUT if primary == BEHEMOTH else SAFE
                st.toast(f"รินสลับสมองเป็นโหมดสำรองเพื่อความรวดเร็วค่ะ ⚡", icon="⚠️")
                
                response = client.chat.completions.create(model=fallback_model, messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:])
                answer = response.choices[0].message.content

            st.markdown(answer)
            if voice_on:
                asyncio.run(make_voice(answer))
                play_audio_hidden("rin_voice.mp3")
            st.session_state.messages.append({"role": "assistant", "content": answer})
