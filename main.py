# --- 1. UI & Persona Setup (ฉบับขยายร่างริน) ---
st.set_page_config(page_title="Rin v38.1 Eternal", layout="centered")

RIN_AVATAR = "rin_avatar.jpg" 

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff !important; }}
    * {{ color: #000000 !important; font-size: 19px; }}
    .stChatMessage {{ background-color: #f8f9fa !important; border-radius: 12px; border: 1px solid #eee; }}
    
    /* 🔴 จุดขยายร่างริน: ปรับขนาดรูป Avatar ในแชทให้ใหญ่ขึ้น */
    [data-testid="stChatMessageElement"] img {{
        width: 65px !important; 
        height: 65px !important;
        border-radius: 10px !important; /* ทำมุมโค้งมนให้ดูแพง */
        border: 2px solid #DDA0DD !important; /* ใส่กรอบสีม่วงประจำตัวริน */
    }}
    
    /* ปรับระยะห่างข้อความไม่ให้ทับรูปที่ใหญ่ขึ้น */
    [data-testid="stChatMessageContent"] {{
        margin-left: 15px !important;
    }}

    .action-container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-bottom: 20px; }}
    .action-chip {{ display: inline-block; padding: 10px 20px; border-radius: 25px; background-color: #f0f2f6; border: 2px solid #DDA0DD; text-decoration: none; color: #000000 !important; font-size: 16px !important; font-weight: bold; transition: 0.3s; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)
