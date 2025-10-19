import streamlit as st
import google.generativeai as genai
import base64, os, json
from gtts import gTTS
from fpdf import FPDF
from datetime import datetime

# ---------- Gemini API Setup ----------
api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password",
                                value=st.secrets.get("GOOGLE_API_KEY", ""))
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

# ---------- UI ----------
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
button[kind="secondary"] {background-color:#2563eb !important; color:white !important; border-radius:10px;}
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

# ---------- Smart Reply ----------
def smart_reply(prompt):
    try:
        sys = "You are EduSmart AI Pro — a bilingual tutor (Bangla/English). Give factual, educational answers clearly."
        r = model.generate_content(sys + "\n\nUser: " + prompt)

        if hasattr(r, "text") and r.text:
            return r.text.strip()

        if hasattr(r, "candidates"):
            texts = []
            for c in r.candidates:
                if hasattr(c, "content") and hasattr(c.content, "parts"):
                    for p in c.content.parts:
                        if hasattr(p, "text") and p.text:
                            texts.append(p.text.strip())
                        elif hasattr(p, "function_call"):
                            texts.append("⚙️ Gemini used an internal function. Please rephrase.")
            if texts:
                return "\n\n".join(texts)

        return str(r)[:800]

    except Exception as e:
        return f"⚠️ সিস্টেম ত্রুটি ঘটেছে: {e}"

# ---------- Chat Display ----------
for role, msg in st.session_state.chat_history[-10:]:
    css = "chat-bubble-user" if role == "user
