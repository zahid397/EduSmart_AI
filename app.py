import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
import base64, tempfile, os
from gtts import gTTS
from fpdf import FPDF
from datetime import datetime

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
    st.markdown(
        f"<audio autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>",
        unsafe_allow_html=True
    )

# ========== Voice Input ==========
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

# ========== UI Setup ==========
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
st.markdown("<h3>Learn • Solve • Search — Powered by Gemini 2.5 Flash ⚡</h3>", unsafe_allow_html=True)

# ========== Chat Memory ==========
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ========== Control Buttons ==========
col_clear, col_pdf, col_voice = st.columns([1,1,2])
with col_clear:
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

with col_pdf:
    if st.button("📄 Save as PDF"):
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
        pdf.cell(200,10,txt="EduSmart AI Pro Chat History", ln=True, align="C")
        pdf.cell(200,10,txt=f"Saved: {datetime.now()}", ln=True); pdf.ln(10)
        for r,m in st.session_state.chat_history:
            prefix = "👤 You:" if r=="user" else "🤖 AI:"
            pdf.multi_cell(0,8,txt=f"{prefix} {m}")
            pdf.ln(2)
        pdf.output("chat_history.pdf")
        with open("chat_history.pdf","rb") as f:
            st.download_button("⬇️ Download Chat PDF", f, "EduSmart_Chat.pdf")

with col_voice:
    if st.button("🎙️ Live Voice Mode"):
        q = listen()
        if q:
            st.session_state.chat_history.append(("user", q))
            st.markdown(f"<div class='chat-bubble-user'>{q}</div>", unsafe_allow_html=True)
            with st.spinner("ভাবছি..."):
                ans = model.generate_content(q).text.strip()
                st.session_state.chat_history.append(("ai", ans))
                st.markdown(f"<div class='chat-bubble-ai'>{ans}</div>", unsafe_allow_html=True)
                speak(ans)
        st.rerun()

# ========== Show Chat History ==========
for role, msg in st.session_state.chat_history[-10:]:
    css = "chat-bubble-user" if role == "user" else "chat-bubble-ai"
    st.markdown(f"<div class='{css}'>{msg}</div>", unsafe_allow_html=True)

# ========== Smart Reply Function ==========
def smart_reply(prompt):
    sys = (
        "You are EduSmart AI Pro — a bilingual smart tutor (Bangla/English). "
        "Use Google Grounding to give factual, correct, clear answers. "
        "Never invent information; if unsure, say you can check online."
    )
    try:
        # ✅ Updated Gemini 2.5 API (no deprecated 'types')
        r = model.generate_content(
            sys + "\n\nUser: " + prompt,
            tools=[{"name": "google_search"}]
        )
        return r.text.strip()
    except Exception as e:
        return f"⚠️ ত্রুটি: {e}"

# ========== Chat Input ==========
if user_input := st.chat_input("তোমার প্রশ্ন লিখো..."):
    st.session_state.chat_history.append(("user", user_input))
    with st.spinner("ভাবছি... 🤔"):
        ans = smart_reply(user_input)
        st.session_state.chat_history.append(("ai", ans))
        st.markdown(f"<div class='chat-bubble-ai'>{ans}</div>", unsafe_allow_html=True)
        speak(ans)
    st.rerun()
