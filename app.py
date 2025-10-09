import os
import requests
import gradio as gr
import tempfile
import fitz
import socket
import speech_recognition as sr
from gtts import gTTS
from openai import OpenAI
from googleapiclient.discovery import build

# === 🔑 API KEYS ===
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

client = OpenAI(api_key=OPENAI_KEY)
CACHE = {}

# === 📘 BOOK LINKS (Google Drive ids) ===
BOOKS = {
    "Bangla": {"id": "1Lz44Rw9btpgvBONTWYtDiagkkBwj_QNw"},
    "English": {"id": "1WS_5YsT7e6vTvv3e1VFEixnOGM1FaTM3"},
    "Math": {"id": "12E6qEgPnF9AwYDwRg24IYwfr8U82MnE5"}
}

def is_online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def read_book(subject, max_chars=100000):
    """Read PDF from local cache or download once from Drive."""
    try:
        file_path = f"{subject.lower()}.pdf"
        if not os.path.exists(file_path):
            link = f"https://drive.google.com/uc?export=download&id={BOOKS[subject]['id']}"
            pdf_data = requests.get(link).content
            with open(file_path, "wb") as f:
                f.write(pdf_data)
        text = []
        with fitz.open(file_path) as doc:
            for p in doc:
                text.append(p.get_text())
                if sum(len(t) for t in text) > max_chars:
                    break
        return "".join(text)
    except Exception as e:
        return f"(Offline Error: {e})"

def speak(text, gender="female", filename="voice.mp3"):
    try:
        prefix = "Male voice: " if gender == "male" else ""
        lang = "bn" if any('\u0980' <= c <= '\u09FF' for c in text) else "en"
        gTTS(text=prefix + text, lang=lang).save(filename)
        return filename
    except Exception:
        return None

def voice_to_text(audio):
    try:
        r = sr.Recognizer()
        with sr.AudioFile(audio) as src:
            data = r.record(src)
        return r.recognize_google(data, language="bn-BD")
    except Exception:
        return ""

def google_search(query):
    try:
        svc = build("customsearch", "v1", developerKey=GOOGLE_KEY)
        res = svc.cse().list(q=query, cx=GOOGLE_CX, num=2).execute()
        out = []
        for item in res.get("items", []):
            out.append(f"📰 **{item['title']}**\n{item['snippet']}\n🔗 {item['link']}")
        return "\n\n".join(out)
    except Exception as e:
        return f"🌐 Google Error: {e}"

def hf_fallback(query):
    try:
        url = "https://api-inference.huggingface.co/models/google/flan-t5-xxl"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        data = {"inputs": f"Answer clearly in Bangla and English: {query}"}
        r = requests.post(url, headers=headers, json=data, timeout=40)
        if r.status_code == 200:
            j = r.json()
            if isinstance(j, list) and j:
                return j[0].get("generated_text", "")
        return ""
    except Exception:
        return ""

def smart_answer(question, subject, audio, speak_enable, gender):
    if not question and audio:
        question = voice_to_text(audio)
    if not question:
        return "⚠️ Please type or say a question.", None

    cache_key = f"{subject}_{question}"
    if cache_key in CACHE:
        ans = CACHE[cache_key]
        return f"📦 Cached:\n{ans}", (speak(ans, gender) if speak_enable else None)

    pdf_text = read_book(subject)
    online = is_online()

    if online:
        # Try OpenAI
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are EduSmart AI, a bilingual tutor."},
                    {"role": "user", "content": f"Subject: {subject}\nContext:\n{pdf_text[:25000]}\n\nQuestion: {question}"}
                ],
                timeout=60
            )
            ans = res.choices[0].message.content
            CACHE[cache_key] = ans
            return "✅ (AI Answer)\n" + ans, (speak(ans, gender) if speak_enable else None)
        except Exception:
            pass
        # Hugging Face fallback
        hf_ans = hf_fallback(question)
        if hf_ans:
            return "✅ (HF Fallback)\n" + hf_ans, (speak(hf_ans, gender) if speak_enable else None)
        # Google fallback
        g_ans = google_search(question)
        return "🌐 (Google Search)\n" + g_ans, None

    else:
        # Offline mode: search within PDF text
        words = [w.lower() for w in question.split() if len(w) > 2]
        sentences = pdf_text.replace("\n", " ").split(". ")
        matched = [s for s in sentences if sum(w in s.lower() for w in words) >= len(words) / 2]
        if matched:
            ans = ". ".join(matched[:3])
            CACHE[cache_key] = ans
            return "📚 (Offline Answer)\n" + ans, (speak(ans, gender) if speak_enable else None)
        return "📴 Offline mode: No match found.", None

def welcome_voice(gender="female"):
    return speak("Welcome to EduSmart AI Ultra. Your smart bilingual tutor!", gender)

def exit_voice(gender="female"):
    return speak("Thank you for using EduSmart AI Ultra. See you again soon!", gender)

with gr.Blocks(title="EduSmart AI Ultra") as demo:
    # Show logo from Hugging Face URL
    gr.Image("https://huggingface.co/spaces/zahid397/EduSmart_AI/resolve/main/logo_.png",
             show_label=False)
    gr.Markdown("# 🎓 EduSmart AI Ultra")

    with gr.Row():
        sub = gr.Dropdown(["Bangla", "English", "Math"], label="📘 Subject", value="Bangla")
        gender = gr.Radio(["male", "female"], label="🎙 Voice Type", value="female")
        voice_on = gr.Checkbox(label="🔊 Voice Reply", value=True)

    gr.Audio(value=welcome_voice("female"), autoplay=True, label="🎵 Welcome")

    q = gr.Textbox(label="Ask Question (Bangla / English)", lines=2)
    audio_in = gr.Audio(label="🎤 Speak Question", type="filepath")
    btn = gr.Button("🚀 Get Answer")

    out_text = gr.Textbox(label="Answer", lines=10)
    out_audio = gr.Audio(label="🔊 Voice Output", type="filepath")

    btn.click(fn=smart_answer,
              inputs=[q, sub, audio_in, voice_on, gender],
              outputs=[out_text, out_audio])

    bye_btn = gr.Button("❌ Exit")
    bye_audio = gr.Audio(label="👋 Goodbye", type="filepath")
    bye_btn.click(fn=lambda g: ("👋 Thank you!", exit_voice(g)),
                  inputs=[gender], outputs=[out_text, bye_audio])

if __name__ == "__main__":
    demo.launch(share=True)