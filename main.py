import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import os, base64, asyncio, edge_tts
from datetime import datetime

# --- 1. UI Setup ---
st.set_page_config(page_title="Rin v35.1 Partner", layout="centered")
st.markdown("<style>.stApp { background-color: #ffffff !important; } * { color: #000000 !important; font-size: 19px; } .stChatMessage { background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; } .crypto-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #DDA0DD; margin-bottom: 15px;}</style>", unsafe_allow_html=True)

# --- 2. Core Logic ---
def encode_image(image_file): return base64.b64encode(image_file.getvalue()).decode('utf-8')

def play_audio_hidden(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)

async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-10%", pitch="+2Hz")
    await communicate.save("rin_voice.mp3")

# --- 3. Sidebar ---
with st.sidebar:
    st.markdown("### 📊 System Dashboard")
    st.success("Brain: Llama 4 Scout 🟢")
    st.success("Vision: Llama 3.2 Stable 🟢")
    search_mode = st.toggle("🔍 โหมดหาข้อมูล (Web Search)", value=False)
    voice_on = st.toggle("🔊 เปิดเสียงเลขา", value=True)
    if st.button("🗑️ ล้างประวัติ"): st.session_state.messages = []; st.rerun()

st.markdown("<h2 style='text-align:center;'>👓 Rin v35.1 Partner</h2>", unsafe_allow_html=True)
st.write("---")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. Input Layer ---
uploaded_file = st.file_uploader("ส่งรูปภาพให้รินวิเคราะห์ (Diana Eyes)", type=["jpg", "jpeg", "png"])
col_mic, col_input = st.columns([1, 6])
with col_mic: audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
prompt = st.chat_input("สั่งการรินได้เลยค่ะบอส...")

final_input = None
user_content = []

if audio:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("temp.wav", "wb") as f: f.write(audio)
        with open("temp.wav", "rb") as f:
            ts = client.audio.transcriptions.create(file=("temp.wav", f.read()), model="whisper-large-v3")
            final_input = ts.text
    except: st.error("ไมค์ขัดข้อง")
elif prompt: final_input = prompt

# --- 5. Brain Layer (Processing) ---
if final_input or uploaded_file:
    if final_input: user_content.append({"type": "text", "text": final_input})
    if uploaded_file:
        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(uploaded_file)}"}})
        st.image(uploaded_file, caption="ประมวลผลดวงตา ML...", width=300)

    display_msg = final_input if final_input else "*(ส่งรูปภาพ)*"
    st.session_state.messages.append({"role": "user", "content": display_msg})
    with st.chat_message("user"): st.markdown(display_msg)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("Diana Mode กำลังประมวลผล..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                
                # บรรทัดสำคัญ: แก้ชื่อรุ่น Vision ให้ถูกต้องตามฐานข้อมูลล่าสุดของ Groq ค่ะ!
                model_to_use = "llama-3.2-11b-vision" if uploaded_file else "llama-4-scout-17b-16e-instruct"
                
                search_info = ""
                if search_mode and final_input:
                    tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
                    s_res = tavily.search(query=final_input, max_results=2)
                    search_info = "\nข้อมูลเสริม: " + " ".join([r['content'] for r in s_res['results']])

                sys_msg = f"คุณคือ 'ริน' AI คู่ระดับ Diana ผู้ดูแลบอสคิริลิ บุคลิกสุขุม นิ่ง ฉลาด ใช้สมอง Llama 4 Scout ลงท้าย ค่ะ/คะ เสมอ {search_info}"

                response = client.chat.completions.create(
                    model=model_to_use,
                    messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": user_content}]
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                if voice_on:
                    asyncio.run(make_voice(answer))
                    play_audio_hidden("rin_voice.mp3")
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Error: {str(e)}")
