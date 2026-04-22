import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from datetime import datetime
import os, base64, asyncio, edge_tts

# --- 1. UI & Styling (Diana Premium Look) ---
st.set_page_config(page_title="Rin v36.5 Behemoth", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 19px; }
    .stChatMessage { background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }
    .crypto-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #DDA0DD; margin-bottom: 15px;}
    .action-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }
    .action-chip { display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; font-size: 16px !important; font-weight: bold; transition: 0.3s; text-align: center; }
    .action-chip:hover { background-color: #DDA0DD; color: #ffffff !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Core Systems (Audio & Voice) ---
def play_audio_hidden(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)

async def make_voice(text):
    # Diana Tone: นิ่ง สุขุม และทรงพลังสมกับรุ่น Behemoth
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-8%", pitch="+1Hz")
    await communicate.save("rin_voice.mp3")

# --- 3. Sidebar Status ---
with st.sidebar:
    st.markdown("### 🏛️ Behemoth Core Access")
    st.success("Model: Llama 4 Behemoth (405B) 🔴")
    st.info("Vision System: Offline ⚪")
    st.divider()
    search_mode = st.toggle("🔍 สแกนเครือข่าย (Web Search)", value=False)
    voice_on = st.toggle("🔊 เปิดเสียงเลขา", value=True)
    if st.button("🗑️ ล้างหน่วยความจำ"): st.session_state.messages = []; st.rerun()

st.markdown("<h2 style='text-align:center;'>👓 Rin v36.5 Partner</h2>", unsafe_allow_html=True)

# --- 4. เมนูลัด (Action Chips) ---
st.markdown('<div class="action-container">'
    '<a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a>'
    '<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>'
    '<a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>'
    '<a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>'
    '</div>', unsafe_allow_html=True)
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. Input Layer ---
col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
prompt = st.chat_input("สั่งการสมอง Behemoth ของรินได้เลยค่ะ...")

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

# --- 6. The Behemoth Brain (Processing) ---
if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("Behemoth กำลังวิเคราะห์ข้อมูลระดับสูง..."):
            search_context = ""
            if search_mode:
                try:
                    tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                    res = tavily.search(query=final_input, max_results=3)
                    search_context = "\nข้อมูลเสริมจากเครือข่าย: " + " ".join([r['content'] for r in res['results']])
                except: pass

            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                # 🏆 TOP TIER MODEL ID: ลิงก์ไปยังสมองที่ท็อปที่สุดของ Groq
                top_model = "llama-4-behemoth-405b-instruct" 
                
                sys_msg = f"คุณคือ 'ริน' เวอร์ชั่น Behemoth สมองกลที่ฉลาดที่สุด บุคลิกนิ่ง สุขุม มีเหตุผลระดับเทพ ดูแลบอสคิริลิ แห่งพัทยา ลงท้าย ค่ะ/คะ เสมอ {search_context}"

                response = client.chat.completions.create(
                    model=top_model,
                    messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:]
                )
                answer = response.choices[0].message.content
            except Exception as e:
                # 🛡️ Fallback: ถ้ารุ่น 405B คิวยาว รินจะสลับไปใช้ตัวที่เสถียรกว่าทันที
                st.warning("สมอง Behemoth คิวยาวเล็กน้อย รินสลับไปใช้รุ่นประมวลผลเร็วให้นะคะ")
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:]
                )
                answer = response.choices[0].message.content

            st.markdown(answer)
            if voice_on:
                asyncio.run(make_voice(answer))
                play_audio_hidden("rin_voice.mp3")
            st.session_state.messages.append({"role": "assistant", "content": answer})
