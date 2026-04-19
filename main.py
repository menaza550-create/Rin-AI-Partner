import streamlit as st
from groq import Groq
from tavily import TavilyClient
from audio_recorder_streamlit import audio_recorder
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os, base64, asyncio, edge_tts, pandas as pd, re

# --- 1. การตั้งค่าหน้าตาแอป ---
st.set_page_config(page_title="Rin v34.8 Business Partner", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] { background-color: #ffffff !important; }
    * { color: #000000 !important; font-size: 20px; }
    .action-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }
    .action-chip { 
        display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; 
        border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; 
        font-size: 16px !important; font-weight: bold; transition: 0.3s; text-align: center; 
    }
    .action-chip:hover { background-color: #DDA0DD; color: #ffffff !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .stChatMessage { background-color: #f8f9fa !important; border: 1px solid #e0e0e0 !important; border-radius: 12px; }
    .crypto-card { background-color: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid #DDA0DD; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ระบบจัดการ Google Sheets (จด + อ่าน + คำนวณ) ---
def get_gsheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gsheets_key"], scopes=scope)
        client = gspread.authorize(creds)
        # มั่นใจว่าชื่อชีตและ Worksheet ตรงกับที่บอสสร้างนะคะ
        return client.open("Rin_Memory").worksheet("customer_data")
    except: return None

def save_to_memory(detail):
    try:
        sheet = get_gsheet()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "บอสคิริลิ", detail])
        return True
    except: return False

def read_last_memory(limit=10):
    try:
        sheet = get_gsheet()
        if not sheet: return "ระบบจำไม่ได้เชื่อมต่อค่ะ"
        data = sheet.get_all_values()
        if len(data) <= 1: return "ยังไม่มีประวัติการจดค่ะ"
        last_rows = data[-limit:]
        return "\n".join([f"- {r[0]}: {r[2]}" for r in last_rows])
    except: return "รินรื้อสมุดจดไม่สำเร็จค่ะ"

# [NEW] ฟังก์ชันคำนวณยอดรวมจากความจำ
def calculate_memory(keyword):
    try:
        sheet = get_gsheet()
        if not sheet: return None
        data = sheet.get_all_records() # ดึงข้อมูลมาเป็น List of Dict
        df = pd.DataFrame(data)
        
        # กรองข้อมูลที่มี keyword (เช่น 'รายจ่าย' หรือ 'LUNC') ในคอลัมน์ Detail
        # สมมติหัวตารางบอสคือ Date, User, Detail
        if 'Detail' in df.columns:
            filtered = df[df['Detail'].str.contains(keyword, na=False)]
            
            # ดึงตัวเลขออกจากข้อความด้วย Regex (เช่น "ค่าข้าว 100" -> 100)
            def extract_num(text):
                nums = re.findall(r'\d+', str(text))
                return float(nums[0]) if nums else 0
            
            total = filtered['Detail'].apply(extract_num).sum()
            return total
        return 0
    except: return 0

# --- 3. ฟังก์ชันร่างริน & เสียง ---
def show_rin():
    path = "1000024544.mp4"
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'''<div style="display:flex;justify-content:center;margin-bottom:15px;"><video width="250" autoplay loop muted playsinline style="border-radius:15px;border:2px solid #DDA0DD;"><source src="data:video/mp4;base64,{b64}" type="video/mp4"></video></div>''', unsafe_allow_html=True)

async def make_voice(text):
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-18%", pitch="+4Hz")
    await communicate.save("rin_voice.mp3")

if "messages" not in st.session_state: st.session_state.messages = []

# --- 4. Sidebar ---
with st.sidebar:
    st.markdown("### 📊 Business Dashboard")
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        p_res = tavily.search(query="LUNC price USD today", max_results=1)
        st.markdown(f'<div class="crypto-card"><b>LUNC Status:</b><br>{p_res["results"][0]["content"][:100]}...</div>', unsafe_allow_html=True)
    except: st.write("⚠️ โหลดราคาเหรียญไม่ได้ค่ะ")
    
    st.divider()
    st.markdown("### Rin Settings 👓")
    think_lvl = st.radio("ระดับการคิด:", ("Standard", "Max Reasoning ✨"))
    voice_on = st.toggle("เปิดเสียงเลขา", value=True)
    
    # ปุ่มทางลัดคำนวณใน Sidebar
    if st.button("💰 สรุปรายจ่ายทั้งหมด"):
        total = calculate_memory("รายจ่าย")
        st.write(f"ยอดรวมรายจ่าย: {total:,.2 dream} บาท")

    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        st.rerun()

show_rin()
st.markdown("<h3 style='text-align:center;'>Rin v34.8 Partner</h3>", unsafe_allow_html=True)

# --- ACTION CHIPS ---
st.markdown('<div class="action-container">'
    '<a href="https://www.google.com/maps" target="_blank" class="action-chip">📍 นำทาง</a>'
    '<a href="https://www.youtube.com" target="_blank" class="action-chip">📺 YouTube</a>'
    '<a href="https://www.facebook.com" target="_blank" class="action-chip">👥 Facebook</a>'
    '<a href="https://line.me/R/" target="_blank" class="action-chip">🟢 Line</a>'
    '</div>', unsafe_allow_html=True)

st.write("---")

# แสดงแชท
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. ส่วนรับคำสั่ง ---
audio = audio_recorder(text="", icon_size="2x", neutral_color="#444444", recording_color="#ff4b4b")
prompt = st.chat_input("คุยกับริน หรือสั่งให้ริน 'จด'/'คำนวณ' ได้เลยค่ะ...")
final_input = None

if audio:
    with st.spinner("..."):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        with open("t.wav", "wb") as f: f.write(audio)
        with open("t.wav", "rb") as f:
            final_input = client.audio.transcriptions.create(file=("t.wav", f.read()), model="whisper-large-v3").text
elif prompt: final_input = prompt

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"): st.markdown(final_input)

    with st.chat_message("assistant", avatar="👓"):
        past_memory = read_last_memory(15)
        
        # Logic: การบันทึก
        if any(w in final_input for w in ["จด", "บันทึก", "จำ"]):
            if save_to_memory(final_input):
                answer = "เรียบร้อยค่ะ! รินจดลง Sheets ให้บอสแล้วนะคะ 👓✨"
            else: answer = "รินจดไม่ได้ค่ะ บอสเช็คสิทธิ์ Sheets หน่อยนะ คะ"
        
        # [NEW] Logic: การคำนวณยอดรวมผ่านแชท
        elif any(w in final_input for w in ["รวมยอด", "สรุปยอด", "คำนวณ"]):
            keyword = "รายจ่าย" # หรือดึงจากคำพูดบอส
            total = calculate_memory(keyword)
            answer = f"บอสคะ จากที่รินไปรื้อสมุดจดมา ยอดรวมของ '{keyword}' ทั้งหมดคือ {total:,.2f} ค่ะ บอสพอใจไหมคะ? 👓💰"
            
        # Logic: การคุยปกติ
        else:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            context = ""
            if "Max" in think_lvl or any(w in final_input for w in ["ราคา", "ข่าว", "เช็ค"]):
                try:
                    search = tavily.search(query=final_input, max_results=3)
                    context = "".join([r['content'] for r in search['results']])
                except: pass
            
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": f"คุณคือริน เลขาบอส Piyawut พัทยา ความจำ: {past_memory} ข้อมูลเน็ต: {context} ตอบหวานๆ ลงท้ายค่ะ/คะ"},
                          *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]]
            )
            answer = chat.choices[0].message.content
        
        st.markdown(answer)
        if voice_on:
            asyncio.run(make_voice(answer))
            st.audio("rin_voice.mp3", autoplay=True)
        st.session_state.messages.append({"role": "assistant", "content": answer})
