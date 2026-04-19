import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
from pyairtable import Api
from datetime import datetime
import os, base64, asyncio, edge_tts

# --- 1. CONFIG & UI (Optimization) ---
st.set_page_config(page_title="Rin v34.8.2 Turbo", layout="centered")

# [NEW] ระบบจำไฟล์วิดีโอ ไม่ต้องโหลดใหม่ทุกรอบ
@st.cache_data
def get_video_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# [NEW] ระบบจำราคา Crypto ไม่ต้องค้นหาทุกวินาที (จำไว้ 10 นาที)
@st.cache_data(ttl=600)
def get_crypto_price(api_key):
    try:
        tavily = TavilyClient(api_key=api_key)
        res = tavily.search(query="LUNC price USD today", max_results=1)
        return res["results"][0]["content"][:80]
    except: return "⚠️ โหลดข้อมูลไม่ได้ค่ะ"

# --- 2. ระบบ Airtable (จูนความเร็ว) ---
def get_airtable():
    return Api(st.secrets["AIRTABLE_TOKEN"]).table(st.secrets["AIRTABLE_BASE_ID"], st.secrets["AIRTABLE_TABLE_NAME"])

def save_memory(u, r):
    try:
        get_airtable().create({"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "User": u, "Rin": r})
        return True
    except: return False

@st.cache_data(ttl=60) # จำความจำล่าสุดไว้ 1 นาที ไม่ต้องอ่านใหม่ทุกวินาที
def read_memory():
    try:
        recs = get_airtable().all(max_records=3, sort=["-Date"])
        return "\n".join([f"- บอสเคยพูด: {r['fields'].get('User')}" for r in recs])
    except: return ""

# --- 3. ฟังก์ชันเสียง ---
async def make_voice(text):
    comm = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await comm.save("rin_voice.mp3")

# --- 4. Sidebar: Dashboard (Turbo Mode) ---
with st.sidebar:
    st.markdown("### 📊 Business Dashboard")
    # เรียกใช้ราคาที่ Cache ไว้ จะทำให้ Sidebar เปิดไวมาก!
    lunc_info = get_crypto_price(st.secrets["TAVILY_API_KEY"])
    st.info(f"**LUNC Status:**\n{lunc_info}...")
    
    st.divider()
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    if st.button("ล้างแชท"):
        st.session_state.messages = []
        st.rerun()

# --- 5. แสดงร่างริน (ใช้ระบบ Cache) ---
v_b64 = get_video_base64("1000024544.mp4")
if v_b64:
    st.markdown(f'''<div style="display:flex;justify-content:center;margin-bottom:15px;"><video width="220" autoplay loop muted playsinline style="border-radius:20px;border:3px solid #DDA0DD;"><source src="data:video/mp4;base64,{v_b64}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

st.markdown("<h3 style='text-align:center;'>Rin v34.8.2 Partner</h3>", unsafe_allow_html=True)

# --- แชทหลัก ---
if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# ส่วนรับคำสั่ง
audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444")
prompt = st.chat_input("สั่งรินได้เลยค่ะบอส...")
final_in = None

if audio:
    with st.spinner("..."):
        try:
            with open("t.wav", "wb") as f: f.write(audio)
            with open("t.wav", "rb") as f:
                final_in = Groq(api_key=st.secrets["GROQ_API_KEY"]).audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text
        except: st.error("ไมค์หลุดค่ะ")
elif prompt: final_in = prompt

if final_in:
    st.session_state.messages.append({"role": "user", "content": final_in})
    with st.chat_message("user"): st.markdown(final_in)

    with st.chat_message("assistant", avatar="👓"):
        with st.spinner("รินประมวลผลแป๊บนึงนะคะ..."):
            mem = read_memory() # อ่านความจำที่ Cache ไว้
            
            # AI Response
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"คุณคือริน เลขาบอสคิริลิ ความจำ: {mem}"}] + st.session_state.messages[-3:]
            )
            ans = chat.choices[0].message.content
            
            # ระบบจดบันทึก
            if any(w in final_in for w in ["จด", "บันทึก"]):
                if save_memory(final_in, ans): ans += "\n\n(จดแล้วค่ะ 📝)"
                st.cache_data.clear() # ล้าง Cache เพื่อให้อ่านความจำใหม่รอบหน้า
            
            st.markdown(ans)
            if voice_on:
                asyncio.run(make_voice(ans))
                st.audio("rin_voice.mp3", autoplay=True)
            st.session_state.messages.append({"role": "assistant", "content": ans})
