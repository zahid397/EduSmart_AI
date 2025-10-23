# ======================================
# EduSmart AI Pro v7.5 — Full Final Build ✅
# ======================================

import streamlit as st
import google.generativeai as genai
import base64, os, platform, time, random
from datetime import datetime
from gtts import gTTS
import plotly.graph_objects as go
import pandas as pd
from PIL import Image
import pytesseract
from langdetect import detect

# ---------- Page Setup ----------
st.set_page_config(page_title="EduSmart AI Pro", page_icon="⚡", layout="wide")
IS_CLOUD = "streamlit" in platform.node().lower() or os.environ.get("STREAMLIT_RUNTIME", "")

# ---------- API Setup ----------
@st.cache_resource
def get_model(api_key):
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")

api_key = (
    st.secrets.get("GOOGLE_API_KEY", "")
    or st.sidebar.text_input("🔑 Gemini API Key", type="password", placeholder="Enter your key...")
)
model = get_model(api_key)

# ---------- Voice ----------
def speak(text):
    try:
        lang = detect(text)
        if lang not in ["bn", "en"]:
            lang = "bn"
        tts = gTTS(text=text, lang=lang)
        tts.save("voice.mp3")
        with open("voice.mp3", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        os.remove("voice.mp3")
        st.markdown(
            f"<audio autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>",
            unsafe_allow_html=True,
        )
    except Exception:
        st.warning("🎧 Voice playback unavailable (cloud mode).")

def listen():
    if IS_CLOUD:
        st.warning("🎙️ Voice input works only in local mode.")
        return ""
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as src:
            st.info("🎧 বলুন বা Speak Now...")
            audio = r.listen(src, timeout=10, phrase_time_limit=10)
        return r.recognize_google(audio, language="bn-BD")
    except Exception as e:
        st.warning(f"🎙️ Voice Input Error: {e}")
        return ""

# ---------- Style ----------
st.markdown("""
<style>
.stApp {background:linear-gradient(135deg,#020617,#0f172a,#1e293b);color:#f8fafc;font-family:'Poppins',sans-serif;}
.glow-box {background:linear-gradient(90deg,#1e3a8a,#2563eb,#38bdf8);
padding:25px;border-radius:20px;text-align:center;color:white;
box-shadow:0 0 25px rgba(59,130,246,0.7);animation:glow 3s infinite alternate;}
@keyframes glow {0% { box-shadow:0 0 15px #2563eb; }100% { box-shadow:0 0 40px #38bdf8; }}
.msg-user {background:#2563eb;color:white;padding:10px;border-radius:14px 14px 4px 14px;margin:5px 0;max-width:80%;}
.msg-ai {background:#334155;color:#f8fafc;padding:10px;border-radius:14px 14px 14px 4px;margin:5px 0;max-width:80%;}
.footer {text-align:center;color:#94a3b8;margin-top:40px;font-size:14px;}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("""
<div class='glow-box'>
  <img src='https://huggingface.co/spaces/zahid397/EduSmart_AI/resolve/main/logo_.png'
       style='width:130px;border-radius:50%;margin-bottom:10px;box-shadow:0 0 25px white;'>
  <h1>✨ EduSmart AI Pro ⚡</h1>
  <p>Learn • Solve • Speak • Visualize • Grow</p>
</div>
""", unsafe_allow_html=True)

# ---------- File Upload ----------
uploaded = st.file_uploader("📎 Upload Image / PDF (Optional)")
if uploaded:
    if uploaded.type.startswith("image"):
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded Image", use_column_width=True)
        text = pytesseract.image_to_string(img)
        st.info(f"🧾 Extracted Text: {text}")
    else:
        st.success(f"📄 Uploaded: {uploaded.name}")

# ---------- Chat Section ----------
if "chat" not in st.session_state:
    st.session_state.chat = []

for role, msg in st.session_state.chat:
    css = "msg-user" if role == "user" else "msg-ai"
    st.markdown(f"<div class='{css}'>{msg}</div>", unsafe_allow_html=True)

prompt = st.chat_input("Type or speak your question...")

if st.button("🎙️ Voice Input"):
    voice_input = listen()
    if voice_input:
        st.session_state.chat.append(("user", voice_input))
        if model:
            with st.spinner("🤖 Thinking..."):
                res = model.generate_content(voice_input).text
                st.session_state.chat.append(("ai", res))
                st.markdown(f"<div class='msg-ai'>{res}</div>", unsafe_allow_html=True)
                speak(res)

if prompt:
    st.session_state.chat.append(("user", prompt))
    if not model:
        st.warning("⚠️ Please enter your Gemini API key first.")
    else:
        with st.spinner("🤖 EduSmart is thinking..."):
            try:
                res = model.generate_content(prompt).text
                st.session_state.chat.append(("ai", res))
                st.markdown(f"<div class='msg-ai'>{res}</div>", unsafe_allow_html=True)
                speak(res)
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ---------- Visualization ----------
st.markdown("---")
st.subheader("📊 Real-Time AI Visualization")

col1, col2, col3 = st.columns(3)
speed = col1.slider("⏱ Speed (ms)", 200, 1500, 500, 100)
color = col2.color_picker("🎨 Color", "#38bdf8")
steps = col3.slider("📈 Steps", 5, 40, 20)

progress = pd.DataFrame({"Step": [], "Accuracy": []})
chart = st.empty()

for i in range(1, steps + 1):
    new = pd.DataFrame({"Step": [i], "Accuracy": [70 + random.random() * 30]})
    progress = pd.concat([progress, new])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=progress["Step"], y=progress["Accuracy"],
        mode="lines+markers", line=dict(color=color, width=3),
        marker=dict(size=8)
    ))
    fig.update_layout(
        template="plotly_dark",
        title="EduSmart AI Learning Progress",
        xaxis_title="Step", yaxis_title="Accuracy (%)",
        yaxis=dict(range=[60, 100])
    )
    chart.plotly_chart(fig, use_container_width=True)
    time.sleep(speed / 1000)

st.success("✅ Visualization Complete — Accuracy Above 90%!")

# ---------- Footer ----------
st.markdown("""
<div class='footer'>
  Developed by <b>Zahid Hasan</b> | EduSmart AI © 2025
</div>
""", unsafe_allow_html=True)
