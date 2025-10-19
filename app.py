import os
import json
import socket
import asyncio
import httpx
import tempfile
import streamlit as st
from gtts import gTTS
import speech_recognition as sr
from sympy import sympify, sqrt, pi
import google.generativeai as genai

# =============================
# 🔑 API Keys
# =============================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
HF_KEY = os.getenv("HUGGINGFACE_API_TOKEN")

# =============================
# ⚙️ Configuration
# =============================
GEMINI_MODEL = "gemini-2.5-flash"
HF_MODEL_URL = "https://api-inference.huggingface.co/models/google/flan-t5-xxl"
SYS_PROMPT = (
    "You are EduSmart AI Tutor. "
    "Answer clearly in Bangla and English with one example. "
    "Keep tone helpful, polite, and educational."
)

# =============================
# 🌐 Internet Check
# =============================
def is_online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except:
        return False

# =============================
# 🎤 Speech → Text
# =============================
def stt(audio_file):
    if not audio_file:
        return ""
    if not is_online():
        return "(Offline: Voice input unavailable.)"
    try:
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as src:
            data = r.record(src)
        return r.recognize_google(data, language="bn-BD")
    except Exception as e:
        return f"(STT Error: {str(e)})"

# =============================
# 🔊 Text → Speech
# =============================
def tts(text):
    if not text:
        return None
    lang = "bn" if any('\u0980' <= c <= '\u09FF' for c in text) else "en"
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            filename = fp.name
        gTTS(text=text, lang=lang).save(filename)
        return filename
    except Exception as e:
        st.warning(f"TTS Error: {e}")
        return None

# =============================
# 🧮 Calculator
# =============================
def calc(expr):
    expr = expr.strip().replace("^", "**").replace("√", "sqrt").replace("π", "pi")
    try:
        result = sympify(expr).evalf()
        return f"🧮 Answer = {result}"
    except:
        return ""

# =============================
# 📘 Offline QnA
# =============================
def load_qna():
    folder = "json_data"
    qna = []
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.endswith(".json"):
                with open(os.path.join(folder, f), encoding="utf-8") as file:
                    qna.extend(json.load(file))
    return qna

QNA = load_qna()

def search_local(q):
    q = q.lower().strip()
    for qa in QNA:
        if qa["question"].lower() in q:
            return qa["answer"]
    return ""

# =============================
# ⚡ Gemini + Hugging Face
# =============================
async def gemini_answer(prompt):
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = await asyncio.to_thread(model.generate_content, prompt)
        return getattr(response, "text", "").strip()
    except Exception as e:
        return f"(Gemini Error: {e})"

async def hf_answer(prompt):
    try:
        headers = {"Authorization": f"Bearer {HF_KEY}"}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(HF_MODEL_URL, headers=headers, json={"inputs": prompt})
        if r.status_code == 200:
            data = r.json()
            return data[0].get("generated_text", "").strip()
    except Exception as e:
        return f"(HF Error: {e})"
    return ""

# =============================
# 🧠 Main Logic
# =============================
async def get_answer(query):
    if not query:
        return "⚠️ Please ask a question."

    # Calculator
    calc_res = calc(query)
    if calc_res:
        return calc_res

    # Offline
    local = search_local(query)
    if local:
        return f"📚 (Offline)\n{local}"

    # Online AI
    if is_online():
        prompt = f"{SYS_PROMPT}\nUser: {query}"
        ai = await gemini_answer(prompt) or await hf_answer(prompt)
        return f"🌐 (AI)\n{ai}" if ai else "⚠️ No AI response found."
    else:
        return "📴 Offline. Connect to Internet."

# =============================
# 🎨 Streamlit UI
# =============================
st.set_page_config(page_title="EduSmart AI — Streamlit", layout="centered")

st.title("🎓 EduSmart AI — Gemini + Hugging Face (Streamlit Version)")
st.markdown("#### 🧠 Bilingual Tutor • Voice • Offline Mode • Calculator")

query = st.text_input("Type your question (বাংলা / English / Math):")
audio_input = st.file_uploader("🎙 Upload voice (optional)", type=["wav", "mp3"])

if st.button("🚀 Ask"):
    if audio_input:
        text = stt(audio_input)
        st.write(f"🎤 Recognized Speech: `{text}`")
        query = query or text

    if query:
        with st.spinner("Thinking... 🤔"):
            ans = asyncio.run(get_answer(query))
        st.success(ans)
        audio_path = tts(ans)
        if audio_path:
            st.audio(audio_path)
    else:
        st.warning("Please type or upload a question!")
