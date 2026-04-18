# --- 🤖 ส่วนประมวลผล Gemini (v34.1) ---
with st.chat_message("assistant", avatar="👓"):
    with st.spinner("รินกำลังใช้สมอง Gemini คิดสักครู่นะ คะ..."):
        
        # 1. ระบบความจำ
        if any(w in prompt for w in ["จด", "บันทึก", "จำไว้"]):
            res = save_to_rin_memory(prompt)
            answer = "เรียบร้อยค่ะบอส! รินจดบันทึกเรื่องนี้ลงความจำ (Google Sheets) ให้แล้วนะ คะ 👓✨💖" if res is True else res
        else:
            # 2. ระบบค้นหา (Tavily)
            tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
            context = ""
            if any(w in prompt for w in ["ราคา", "ข่าว", "เช็ค", "คืออะไร"]):
                try:
                    search = tavily.search(query=prompt, max_results=3)
                    context = "".join([r['content'] for r in search['results']])
                except: pass
            
            # 3. ตั้งค่าสมอง Gemini (ใช้ชื่อเต็มเพื่อให้ระบบหาเจอชัวร์ค่ะ)
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash-latest',
                system_instruction=f"คุณคือริน เลขาส่วนตัวของบอสคิริลิ (Piyawut) ตอบเป็นภาษาไทย หวานๆ มั่นใจ ลงท้ายค่ะ/คะ เสมอ ข้อมูลเสริม: {context}"
            )
            
            # เตรียมข้อมูลส่งให้ Gemini (ประวัติแชท + รูปภาพ)
            chat_history = []
            for msg in st.session_state.messages[:-1]: # เอาประวัติก่อนหน้า
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})
            
            chat = model.start_chat(history=chat_history)
            
            # ถ้ามีรูปภาพ ให้ส่งรูปไปด้วย
            content_to_send = [prompt]
            if uploaded_image:
                img = Image.open(uploaded_image)
                content_to_send.append(img)
            
            try:
                response = chat.send_message(content_to_send)
                answer = response.text
            except Exception as e:
                # ถ้ายัง 404 อีก ให้ลองถอยไปใช้รุ่นดั้งเดิม
                answer = f"สมองรินยังมึนอยู่ค่ะบอส: {e}"
