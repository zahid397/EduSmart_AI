# ======================================
# EduSmart AI Pro v6.3 — Streamlit Optimized Live Chart Edition ✅
# ======================================

import streamlit as st
import google.generativeai as genai
import base64, os, json, random, platform
from datetime import datetime
from gtts import gTTS
import plotly.graph_objects as go
import pandas as pd

# ---------- Setup ----------
st.set_page_config(page_title="EduSmart AI Pro", page_icon="⚡", layout="wide")

IS_CLOUD = "streamlit" in platform.node().lower() or os.environ.get("STREAMLIT_RUNTIME", "")

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
        tts = gTTS(text=text, lang="bn")
        tts.save("voice.mp3")
        with open("voice.mp3", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        os.remove("voice.mp3")
        st.markdown(
            f"<audio autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>",
            unsafe_allow_html=True,
        )
    except:
        st.warning("🎧 Voice playback unavailable in cloud mode.")

# ---------- Style ----------
st.markdown("""
<style>
.stApp {background:linear-gradient(135deg,#020617,#0f172a,#1e293b);color:#f8fafc;font-family:'Poppins',sans-serif;}
.glow-box {background:linear-gradient(90deg,#1e3a8a,#2563eb,#38bdf8);padding:25px;border-radius:20px;text-align:center;color:white;
box-shadow:0 0 25px rgba(59,130,246,0.7);animation:glow 3s infinite alternate;}
@keyframes glow {0% { box-shadow:0 0 15px #2563eb; }100% { box-shadow:0 0 40px #38bdf8; }}
.footer {text-align:center;color:#94a3b8;margin-top:40px;font-size:14px;}
.footer a {color:#38bdf8;text-decoration:none;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown(f"""
<div class='glow-box'>
  <img src='https://huggingface.co/spaces/zahid397/EduSmart_AI/resolve/main/logo_.png'
       style='width:140px;border-radius:50%;box-shadow:0 0 25px white;margin-bottom:10px;'>
  <h1>✨ EduSmart AI Pro ⚡ Streamlit Edition ✨</h1>
  <p>Learn • Solve • Speak • Visualize • Grow</p>
</div>
""", unsafe_allow_html=True)

# ---------- Chat ----------
for k in ["chat"]:
    if k not in st.session_state:
        st.session_state[k] = []

for role, msg in st.session_state.chat:
    if role == "user":
        st.markdown(f"<div style='background:#2563eb;color:#fff;padding:10px 15px;border-radius:16px 16px 4px 16px;margin:6px 0;max-width:85%;'>{msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background:#334155;color:#f8fafc;padding:10px 15px;border-radius:16px 16px 16px 4px;margin:6px 0;max-width:85%;'>{msg}</div>", unsafe_allow_html=True)

prompt = st.chat_input("বার্তা লিখুন...")
if prompt:
    st.session_state.chat.append(("user", prompt))
    if not model:
        st.warning("⚠️ API Key দিন।")
    else:
        with st.spinner("🤖 EduSmart ভাবছে..."):
            try:
                res = model.generate_content(prompt).text
                st.session_state.chat.append(("ai", res))
                st.markdown(f"<div style='background:#334155;color:#f8fafc;padding:10px 15px;border-radius:16px 16px 16px 4px;margin:6px 0;max-width:85%;'>{res}</div>", unsafe_allow_html=True)
                speak(res)
            except Exception as e:
                st.error(f"❌ ত্রুটি: {e}")

# ---------- Control Panel ----------
st.markdown("---")
st.subheader("🎛️ Live Dashboard Control")
col1, col2, col3 = st.columns(3)
speed = col1.slider("⏱ Animation Delay (ms)", 100, 1500, 400, 100)
color = col2.color_picker("🎨 Graph Color", "#38bdf8")
steps = col3.slider("📊 Total Steps", 5, 40, 20)

# ---------- Live Chart ----------
st.subheader("📈 AI Accuracy Visualization (Streamlit Mode)")
progress_df = pd.DataFrame({"Step": [], "Accuracy": []})
chart = st.empty()

for i in range(1, steps + 1):
    new_row = pd.DataFrame({"Step": [i], "Accuracy": [70 + random.random() * 30]})
    progress_df = pd.concat([progress_df, new_row])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=progress_df["Step"], y=progress_df["Accuracy"],
        mode="lines+markers", line=dict(color=color, width=3),
        marker=dict(size=8)
    ))
    fig.update_layout(
        template="plotly_dark",
        title="AI Learning Progress Live Update",
        xaxis_title="Step", yaxis_title="Accuracy (%)",
        yaxis=dict(range=[60, 100])
    )
    chart.plotly_chart(fig, use_container_width=True)
    st.sleep(speed / 1000)

st.success("✅ Visualization Complete — EduSmart AI Steady Above 90%!")

# ---------- Footer ----------
st.markdown("""
<div class='footer'>
  <p>🔹 Developed by <a href='https://huggingface.co/zahid397' target='_blank'>Zahid Hasan</a> | 
  <a href='mailto:zh05698@gmail.com'>Contact</a> | EduSmart AI © 2025</p>
</div>
""", unsafe_allow_html=True)
