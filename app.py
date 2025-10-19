import os
import json
import math
import socket
import asyncio
import httpx
import tempfile
import gradio as gr
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
async def stt(audio_path):
    if not audio_path:
        return ""
    if not is_online():
        return "(Offline: Voice input unavailable. Use text instead.)"
    try:
        loop = asyncio.get_running_loop()

        def _recognize(path):
            r = sr.Recognizer()
            with sr.AudioFile(path) as src:
                data = r.record(src)
            return r.recognize_google(data, language="bn-BD")

        return await loop.run_in_executor(None, _recognize, audio_path)
    except Exception as e:
        return f"(STT Error: {str(e)})"

# =============================
# 🔊 Text → Speech
# =============================
async def tts(text):
    if not text:
        return None
    lang = "bn" if any('\u0980' <= c <= '\u09FF' for c in text) else "en"
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            filename = fp.name
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, gTTS(text=text, lang=lang).save, filename)
        return filename
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

# =============================
# 🧮 Safe Calculator
# =============================
def calc(expr):
    expr = expr.strip()
    if not expr:
        return ""
    expr = expr.replace("^", "**").replace("√", "sqrt").replace("π", "pi")
    try:
        result = sympify(expr).evalf()
        return f"🧮 Answer = {result}"
    except:
        return ""

# =============================
# 📘 Offline QnA Loader
# =============================
def load_qna():
    folder = "json_data"
    qna = []
    if not os.path.exists(folder):
        print("⚠️ 'json_data' folder not found — Offline mode disabled.")
        return []
    for f in os.listdir(folder):
        if f.endswith(".json"):
            try:
                with open(os.path.join(folder, f), encoding="utf-8") as file:
                    qna.extend(json.load(file))
            except Exception as e:
                print(f"JSON Load Error ({f}): {e}")
    return qna

QNA = load_qna()

def search_local(q):
    q = q.lower().strip()
    for qa in QNA:
        if qa["question"].lower() in q:
            return qa["answer"]
    return ""

# =============================
# ⚡ Gemini API (Async)
# =============================
async def gemini_answer(prompt):
    if not GEMINI_KEY:
        return ""
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = await asyncio.to_thread(model.generate_content, prompt)
        return getattr(response, "text", "").strip()
    except Exception as e:
        return f"(Gemini Error: {str(e)})"

# =============================
# 🤗 Hugging Face API (Async)
# =============================
async def hf_answer(prompt):
    if not HF_KEY:
        return ""
    try:
        headers = {"Authorization": f"Bearer {HF_KEY}"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(HF_MODEL_URL, headers=headers, json={"inputs": prompt})
        if response.status_code == 200:
            data = response.json()
            return data[0].get("generated_text", "").strip()
        return ""
    except Exception as e:
        return f"(HF Error: {str(e)})"

# =============================
# 🧠 Main Answer Logic
# =============================
async def answer(history, query, audio=None):
    if not query and audio:
        query = await stt(audio)
    if not query:
        return history + [[None, "⚠️ Please type or speak your question."]], ""

    if query.startswith("("):  # Error from STT
        return history + [[None, query]], query

    calc_res = calc(query)
    if calc_res:
        return history + [[query, calc_res]], calc_res

    local = search_local(query)
    if local:
        res = f"📚 (Offline)\n{local}"
        return history + [[query, res]], local

    if is_online():
        prompt = f"{SYS_PROMPT}\nUser: {query}"
        ai = await gemini_answer(prompt) or await hf_answer(prompt)
        if ai:
            res = f"🌐 (AI)\n{ai}"
            return history + [[query, res]], ai
        else:
            res = "⚠️ No AI response found."
            return history + [[query, res]], res
    else:
        res = "📴 Offline. Connect to the Internet or use offline data."
        return history + [[query, res]], res

# =============================
# 💬 Gradio Interface (Async Ready)
# =============================
with gr.Blocks(title="EduSmart AI — Gemini + Hugging Face (Async)", theme=gr.themes.Soft()) as demo:
    gr.HTML("""
    <h1 style='text-align:center;color:#0070f3;'>🎓 EduSmart AI — Async Gemini + Hugging Face</h1>
    <p style='text-align:center;'>Smart Bilingual Tutor • Offline Mode • Voice • Calculator</p>
    <style>
    .textbox { font-family: 'Noto Sans Bengali', sans-serif; }
    </style>
    """)

    chatbot = gr.Chatbot(height=480, show_label=False)
    query = gr.Textbox(label="Ask (বাংলা / English / Math)", placeholder="Type or Speak…", elem_classes=["textbox"])
    audio_in = gr.Audio(label="🎙 Speak", type="filepath")
    send = gr.Button("🚀 Send")
    clear = gr.Button("🧹 Clear")
    audio_out = gr.Audio(label="🔊 Listen", type="filepath")

    async def respond(history, query, audio_in):
        new_history, final_res = await answer(history, query, audio_in)
        voice = await tts(final_res)
        return new_history, "", voice

    send.click(respond, [chatbot, query, audio_in], [chatbot, query, audio_out])
    clear.click(lambda: ([], "", None), outputs=[chatbot, query, audio_out])

if __name__ == "__main__":
    demo.queue().launch(share=True)
