import streamlit as st
import google.generativeai as genai
import base64, os
from gtts import gTTS
from fpdf import FPDF
from datetime import datetime

# ---------- API setup ----------
api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password", value=st.secrets.get("GOOGLE_API_KEY", ""))
if api_key:
    genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------- Voice ----------
def speak(text):
    tts = gTTS(text=text, lang="bn")
    tts.save("temp.mp3")
    with open("temp.mp3", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.remove("temp.mp3")
    st.markdown(f"<audio autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>", unsafe_allow_html=True)

def play_welcome_voice():
    msg = "হ্যালো! আমি এডুস্মার্ট এআই প্রো। কীভাবে সাহায্য করতে পারি?"
    tts = gTTS(text=msg, lang="bn")
    tts.save("welcome.mp3")
    with open("welcome.mp3", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.remove("welcome.mp3")
    st.markdown(f"<audio autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>", unsafe_allow_html=True)

# ---------- Page setup ----------
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

if os.path.exists("logo.png"):
    st.image("logo.png", width=180)
st.markdown("<h1>🏆 EduSmart AI Pro 💡</h1>", unsafe_allow_html=True)
st.markdown("<h3>Learn • Solve • Search — Powered by Gemini 2.5 Flash ⚡</h3>", unsafe_allow_html=True)

play_welcome_voice()

# ---------- Memory ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------- Smart reply ----------
def smart_reply(prompt):
    sys = ("You are EduSmart AI Pro — a bilingual tutor (Bangla/English). "
           "Give clear, factual answers using web knowledge when needed.")
    try:
        r = model.generate_content(sys + "\n\nUser: " + prompt, tools=[{"name": "google_search"}])
        if hasattr(r, "text") and r.text:
            return r.text.strip()
        if hasattr(r, "candidates"):
            for c in r.candidates:
                if hasattr(c, "content") and hasattr(c.content, "parts"):
                    for p in c.content.parts:
                        if hasattr(p, "text") and p.text:
                            return p.text.strip()
                        elif hasattr(p, "function_call"):
                            return "⚙️ Gemini is processing a function call — try rephrasing."
        return "🤔 আমি নিশ্চিত নই, প্রশ্নটা একটু ভিন্নভাবে বলো।"
    except Exception as e:
        return f"⚠️ ত্রুটি: {e}"

# ---------- Chat ----------
for role, msg in st.session_state.chat_history[-10:]:
    css = "chat-bubble-user" if role == "user" else "chat-bubble-ai"
    st.markdown(f"<div class='{css}'>{msg}</div>", unsafe_allow_html=True)

if user_input := st.chat_input("তোমার প্রশ্ন লিখো..."):
    st.session_state.chat_history.append(("user", user_input))
    with st.spinner("ভাবছি... 🤔"):
        ans = smart_reply(user_input)
        st.session_state.chat_history.append(("ai", ans))
        st.markdown(f"<div class='chat-bubble-ai'>{ans}</div>", unsafe_allow_html=True)
        speak(ans)
    st.rerun()

# ---------- Save PDF ----------
if st.button("📄 Save Chat as PDF"):
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
    pdf.cell(200,10,"EduSmart AI Pro Chat History",ln=True,align="C")
    for r,m in st.session_state.chat_history:
        prefix = "👤 You:" if r=="user" else "🤖 AI:"
        pdf.multi_cell(0,8,f"{prefix} {m}")
        pdf.ln(2)
    pdf.output("chat.pdf")
    with open("chat.pdf","rb") as f:
        st.download_button("⬇️ Download PDF", f, "EduSmart_Chat.pdf")
