import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
import base64, tempfile, os, smtplib, threading
from gtts import gTTS
from fpdf import FPDF
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# ========== Gemini 2.5 Flash Setup ==========
api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password",
                                value=st.secrets.get("GOOGLE_API_KEY", ""))
if api_key:
    genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

# ========== Voice Output ==========
def speak(text):
    """Generate speech using Google TTS (Cloud compatible)"""
    tts = gTTS(text=text, lang="bn")
    tts.save("temp.mp3")
    with open("temp.mp3", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.remove("temp.mp3")
    st.markdown(f"<audio autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>", unsafe_allow_html=True)

# ========== Voice Input ==========
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as src:
        st.info("🎧 বলো, আমি শুনছি...")
        audio = r.listen(src, timeout=5, phrase_time_limit=8)
    try:
        return r.recognize_google(audio, language="bn-BD")
    except:
        return ""

# ========== UI ==========
st.set_page_config(page_title="EduSmart AI Pro", page_icon="💡", layout="centered")
st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#020617,#0f172a,#1e293b);
color:#f8fafc;font-family:'Poppins',sans-serif;}
.chat-bubble-user{background:#2563eb;color:#fff;padding:10px 16px;
border-radius:16px 16px 4px 16px;margin:6px 0;max-width:85%;display:inline-block;}
.chat-bubble-ai{background:#334155;color:#f8fafc;padding:10px 16px;
border-radius:16px 16px 16px 4px;margin:6px 0;max-width:85%;display:inline-block;}
h1,h3{text-align:center;color:#38bdf8;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>EduSmart AI Pro 💡</h1>", unsafe_allow_html=True)
st.markdown("<h3>Learn • Solve • Talk — Now with Live Conversation Mode ⚡</h3>", unsafe_allow_html=True)

# ========== Chat Memory ==========
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ========== Smart Reply ==========
def smart_reply(prompt):
    sys = (
        "You are EduSmart AI Pro — a bilingual smart tutor (Bangla/English). "
        "Use Google Grounding to give factual, correct, clear answers. "
        "Never invent information; if unsure, say you can check online."
    )
    try:
        r = model.generate_content(sys + "\n\nUser: " + prompt, tools=[{"name": "google_search"}])
        if hasattr(r, "text") and r.text:
            return r.text.strip()
        else:
            try:
                return r.candidates[0].content.parts[0].text.strip()
            except Exception:
                return "⚠️ উত্তর প্রাপ্তিতে সমস্যা হয়েছে। আবার চেষ্টা করো।"
    except Exception as e:
        return f"⚠️ ত্রুটি: {e}"

# ========== Live Conversation Mode ==========
def live_conversation():
    st.info("🎙️ Live Conversation শুরু হচ্ছে... (Ctrl+C চাপলে বন্ধ হবে)")
    while True:
        try:
            user_voice = listen()
            if not user_voice:
                continue
            st.session_state.chat_history.append(("user", user_voice))
            st.markdown(f"<div class='chat-bubble-user'>{user_voice}</div>", unsafe_allow_html=True)
            ai_reply = smart_reply(user_voice)
            st.session_state.chat_history.append(("ai", ai_reply))
            st.markdown(f"<div class='chat-bubble-ai'>{ai_reply}</div>", unsafe_allow_html=True)
            speak(ai_reply)
        except KeyboardInterrupt:
            st.warning("🛑 Conversation বন্ধ হয়েছে।")
            break
        except Exception as e:
            st.error(f"ত্রুটি: {e}")
            break

# ========== Buttons ==========
col_clear, col_pdf, col_voice, col_para, col_email, col_live = st.columns([1,1,1,1,1,1])
with col_clear:
    if st.button("🗑️ Clear"):
        st.session_state.chat_history = []; st.rerun()
with col_pdf:
    if st.button("📄 Save PDF"):
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
        pdf.cell(200,10,"EduSmart AI Pro Chat History",ln=True,align="C")
        pdf.cell(200,10,f"Saved: {datetime.now()}",ln=True); pdf.ln(10)
        for r,m in st.session_state.chat_history:
            prefix="👤 You:" if r=="user" else "🤖 AI:"
            pdf.multi_cell(0,8,f"{prefix} {m}"); pdf.ln(2)
        pdf.output("chat.pdf")
        with open("chat.pdf","rb") as f:
            st.download_button("⬇️ Download PDF",f,"EduSmart_Chat.pdf")
with col_voice:
    if st.button("🎤 Voice Mode"):
        q = listen()
        if q:
            st.session_state.chat_history.append(("user", q))
            st.markdown(f"<div class='chat-bubble-user'>{q}</div>", unsafe_allow_html=True)
            with st.spinner("ভাবছি..."):
                ans = smart_reply(q)
                st.session_state.chat_history.append(("ai", ans))
                st.markdown(f"<div class='chat-bubble-ai'>{ans}</div>", unsafe_allow_html=True)
                speak(ans)
        st.rerun()
with col_para:
    topic = st.text_input("✍️ Paragraph Topic")
    if st.button("Generate Paragraph"):
        prompt = f"বিষয়: {topic}\nএকটি সুন্দর, গঠনমূলক বাংলা অনুচ্ছেদ লেখো।"
        ans = model.generate_content(prompt).text.strip()
        st.markdown(f"### 📝 Paragraph on '{topic}'\n\n{ans}")
        speak(ans)
with col_email:
    if st.button("📧 Send Email"):
        st.session_state["email_mode"] = True
with col_live:
    if st.button("🎙️ Live Conversation"):
        st.info("🎧 Listening mode enabled. Speak to start talking...")
        thread = threading.Thread(target=live_conversation)
        thread.start()

# ========== Show Chat ==========
for r,m in st.session_state.chat_history[-10:]:
    css="chat-bubble-user" if r=="user" else "chat-bubble-ai"
    st.markdown(f"<div class='{css}'>{m}</div>",unsafe_allow_html=True)

# ========== Email Sending ==========
if "email_mode" in st.session_state and st.session_state["email_mode"]:
    st.markdown("### ✉️ Send Chat to Email")
    to_email=st.text_input("Recipient Email")
    sender=st.text_input("Your Gmail")
    password=st.text_input("App Password (Gmail)",type="password")
    if st.button("Send Now"):
        try:
            pdf=FPDF(); pdf.add_page(); pdf.set_font("Arial",size=12)
            pdf.cell(200,10,"EduSmart AI Pro Chat History",ln=True,align="C")
            for r,m in st.session_state.chat_history:
                prefix="👤 You:" if r=="user" else "🤖 AI:"
                pdf.multi_cell(0,8,f"{prefix} {m}"); pdf.ln(2)
            pdf.output("chat_email.pdf")
            msg=MIMEMultipart(); msg["From"]=sender; msg["To"]=to_email
            msg["Subject"]="EduSmart AI Pro Chat History"
            msg.attach(MIMEText("Here’s your chat history.","plain"))
            with open("chat_email.pdf","rb") as f:
                part=MIMEApplication(f.read(),Name="EduSmart_Chat.pdf")
            part['Content-Disposition']='attachment; filename="EduSmart_Chat.pdf"'
            msg.attach(part)
            with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
                server.login(sender,password)
                server.send_message(msg)
            st.success("📨 Email sent successfully!")
        except Exception as e:
            st.error(f"❌ Failed to send email: {e}")
        st.session_state["email_mode"]=False
