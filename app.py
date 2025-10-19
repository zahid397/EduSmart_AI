import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
import base64, os, smtplib, threading
from gtts import gTTS
from fpdf import FPDF
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# ================== Gemini 2.5 Flash Setup ==================
api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password",
                                value=st.secrets.get("GOOGLE_API_KEY", ""))
if api_key:
    genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

# ================== Voice Output ==================
def speak(text):
    """Google TTS (Streamlit Safe)"""
    tts = gTTS(text=text, lang="bn")
    tts.save("temp.mp3")
    with open("temp.mp3", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.remove("temp.mp3")
    st.markdown(
        f"<audio autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>",
        unsafe_allow_html=True
    )

# ================== Voice Input ==================
def listen():
    """Live mic listening"""
    r = sr.Recognizer()
    with sr.Microphone() as src:
        st.info("🎧 বলো, আমি শুনছি...")
        audio = r.listen(src, timeout=5, phrase_time_limit=8)
    try:
        return r.recognize_google(audio, language="bn-BD")
    except:
        return ""

# ================== UI Setup ==================
st.set_page_config(page_title="EduSmart AI Pro", page_icon="💡", layout="centered")
st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#020617,#0f172a,#1e293b);
color:#f8fafc;font-family:'Poppins',sans-serif;}
.chat-bubble-user{background:#2563eb;color:#fff;padding:10px 16px;border-radius:16px 16px 4px 16px;margin:6px 0;max-width:85%;display:inline-block;}
.chat-bubble-ai{background:#334155;color:#f8fafc;padding:10px 16px;border-radius:16px 16px 16px 4px;margin:6px 0;max-width:85%;display:inline-block;}
h1,h3{text-align:center;color:#38bdf8;}
</style>
""", unsafe_allow_html=True)

# Optional Logo
if os.path.exists("logo.png"):
    st.image("logo.png", width=180)
st.markdown("<h1>🏆 EduSmart AI Pro Ultimate 💡</h1>", unsafe_allow_html=True)
st.markdown("<h3>Chat • Learn • Talk • Write — Powered by Gemini 2.5 Flash ⚡</h3>", unsafe_allow_html=True)

# ================== Chat Memory ==================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ================== AI Smart Reply ==================
def smart_reply(prompt):
    sys = (
        "You are EduSmart AI Pro — a bilingual smart tutor (Bangla/English). "
        "Give accurate, helpful, factual answers using Google Grounding. "
        "If you don’t know, say so clearly."
    )
    try:
        r = model.generate_content(
            sys + "\n\nUser: " + prompt,
            tools=[{"name": "google_search"}]
        )

        # ✅ Robust function-call safe parsing
        if hasattr(r, "text") and r.text:
            return r.text.strip()
        elif hasattr(r, "candidates"):
            for c in r.candidates:
                for p in getattr(c.content, "parts", []):
                    if hasattr(p, "text"):
                        return p.text.strip()
        elif hasattr(r, "function_call") or "function_call" in str(r):
            return "⚙️ Gemini used a function internally. Please rephrase your question."
        else:
            return "🤔 আমি নিশ্চিত নই, প্রশ্নটা একটু ভিন্নভাবে বলো।"

    except Exception as e:
        return f"⚠️ ত্রুটি: {e}"

# ================== Live Conversation ==================
def live_conversation():
    st.info("🎙️ লাইভ কথোপকথন শুরু হয়েছে! (Ctrl+C দিলে বন্ধ হবে)")
    while True:
        try:
            user_voice = listen()
            if not user_voice:
                continue
            st.session_state.chat_history.append(("user", user_voice))
            st.markdown(f"<div class='chat-bubble-user'>{user_voice}</div>", unsafe_allow_html=True)
            reply = smart_reply(user_voice)
            st.session_state.chat_history.append(("ai", reply))
            st.markdown(f"<div class='chat-bubble-ai'>{reply}</div>", unsafe_allow_html=True)
            speak(reply)
        except KeyboardInterrupt:
            st.warning("🛑 Conversation বন্ধ হয়েছে।")
            break
        except Exception as e:
            st.error(f"ত্রুটি: {e}")
            break

# ================== Top Controls ==================
col_clear, col_pdf, col_para, col_email, col_live = st.columns([1,1,1,1,1])
with col_clear:
    if st.button("🧹 Clear"):
        st.session_state.chat_history = []
        st.rerun()
with col_pdf:
    if st.button("📄 Save PDF"):
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
        pdf.cell(200,10,"EduSmart AI Pro Chat History",ln=True,align="C")
        pdf.cell(200,10,f"Saved: {datetime.now()}",ln=True); pdf.ln(10)
        for r,m in st.session_state.chat_history:
            prefix = "👤 You:" if r=="user" else "🤖 AI:"
            pdf.multi_cell(0,8,f"{prefix} {m}")
            pdf.ln(2)
        pdf.output("chat.pdf")
        with open("chat.pdf","rb") as f:
            st.download_button("⬇️ Download Chat PDF", f, "EduSmart_Chat.pdf")

with col_para:
    topic = st.text_input("✍️ Paragraph Topic")
    if st.button("Generate Paragraph"):
        prompt = f"বিষয়: {topic}\nএকটি সুন্দর ও প্রাঞ্জল বাংলা অনুচ্ছেদ লেখো।"
        ans = smart_reply(prompt)
        st.markdown(f"### 📝 Paragraph on '{topic}'\n\n{ans}")
        speak(ans)

with col_email:
    if st.button("📧 Send Email"):
        st.session_state["email_mode"] = True
with col_live:
    if st.button("🎙️ Live Conversation"):
        threading.Thread(target=live_conversation).start()

# ================== Show Chat ==================
for role, msg in st.session_state.chat_history[-10:]:
    css = "chat-bubble-user" if role == "user" else "chat-bubble-ai"
    st.markdown(f"<div class='{css}'>{msg}</div>", unsafe_allow_html=True)

# ================== Chat Input ==================
if user_input := st.chat_input("তোমার প্রশ্ন লিখো বা কিছু বলো..."):
    st.session_state.chat_history.append(("user", user_input))
    with st.spinner("ভাবছি... 🤔"):
        ans = smart_reply(user_input)
        st.session_state.chat_history.append(("ai", ans))
        st.markdown(f"<div class='chat-bubble-ai'>{ans}</div>", unsafe_allow_html=True)
        speak(ans)
    st.rerun()

# ================== Email Send ==================
if "email_mode" in st.session_state and st.session_state["email_mode"]:
    st.markdown("### ✉️ Send Chat to Email")
    to_email = st.text_input("Recipient Email")
    sender = st.text_input("Your Gmail")
    password = st.text_input("App Password (Gmail)", type="password")
    if st.button("Send Now"):
        try:
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
            pdf.cell(200,10,"EduSmart AI Pro Chat History",ln=True,align="C")
            for r,m in st.session_state.chat_history:
                prefix = "👤 You:" if r=="user" else "🤖 AI:"
                pdf.multi_cell(0,8,f"{prefix} {m}"); pdf.ln(2)
            pdf.output("chat_email.pdf")

            msg = MIMEMultipart(); msg["From"]=sender; msg["To"]=to_email
            msg["Subject"]="EduSmart AI Pro Chat History"
            msg.attach(MIMEText("Here’s your EduSmart chat history.","plain"))
            with open("chat_email.pdf","rb") as f:
                part = MIMEApplication(f.read(), Name="EduSmart_Chat.pdf")
            part['Content-Disposition']='attachment; filename="EduSmart_Chat.pdf"'
            msg.attach(part)

            with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
                server.login(sender,password)
                server.send_message(msg)

            st.success("📨 Email sent successfully!")
        except Exception as e:
            st.error(f"❌ Failed to send email: {e}")
        st.session_state["email_mode"] = False
