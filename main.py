with st.chat_message("assistant", avatar="👓"):
        with st.spinner("Diana กำลังสื่อสารกับสมองกล..."):
            try:
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                
                # --- จุดที่ต้องเช็คชื่อรุ่น (Update ตามระบบ Groq ล่าสุด) ---
                vision_model = "llama-3.2-11b-vision-preview" # หรือลอง "llama-3.2-11b-vision"
                text_model = "llama-3.3-70b-versatile"        # รุ่นนี้เสถียรสุดใน Groq ตอนนี้ค่ะ
                
                # ถ้าบอสอยากลอง Llama 4 Scout ให้เปลี่ยน text_model เป็น "llama-4-scout-17b-16e-instruct" 
                # แต่ถ้ามัน 404 ให้กลับมาใช้ 3.3-70b แทนค่ะ
                
                model_to_use = vision_model if uploaded_file else text_model
                
                # --- ระบบเรียกใช้งานพร้อม Fallback (กันพัง 100%) ---
                try:
                    response = client.chat.completions.create(
                        model=model_to_use,
                        messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": user_content}],
                        max_tokens=1024
                    )
                except Exception as e:
                    # ถ้ารุ่นที่เลือก (Scout/Vision) พัง รินจะสลับไปใช้รุ่น Llama 3.3-70b ที่ชัวร์กว่าให้ทันทีค่ะ
                    st.warning(f"⚠️ รุ่น {model_to_use} ไม่พร้อมใช้งาน รินสลับไปใช้สมองสำรองให้นะคะ")
                    safe_model = "llama-3.3-70b-versatile"
                    
                    # ปรับเนื้อหาให้เป็น Text อย่างเดียวเพื่อป้องกัน Error ซ้ำซ้อน
                    safe_content = [{"type": "text", "text": final_input if final_input else "ช่วยวิเคราะห์ข้อมูลในรูปนี้ให้หน่อยค่ะ"}]
                    
                    response = client.chat.completions.create(
                        model=safe_model,
                        messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": safe_content}],
                        max_tokens=1024
                    )
                
                answer = response.choices[0].message.content
                st.markdown(answer)
                
                if voice_on:
                    asyncio.run(make_voice(answer))
                    play_audio_hidden("rin_voice.mp3")
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as final_e:
                st.error(f"❌ ระบบขัดข้องขั้นรุนแรง: {str(final_e)}")
