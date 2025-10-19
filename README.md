EduSmart AI — Bilingual AI Tutor (Gemini + Hugging Face + Offline)

🌐 Live Demo

(তুই deploy করার পর এখানে লিংকটা বসাবি)
👉 Live on Streamlit / Hugging Face


---

📖 About the Project

EduSmart AI হলো একটি AI-পাওয়ার্ড শিক্ষা সহায়ক অ্যাপ, যা বাংলা ও ইংরেজি দুই ভাষাতেই কাজ করে।
এটি ছাত্রদের প্রশ্নের উত্তর দেয়, গণিতের হিসাব করে, অফলাইন ডেটা থেকে উত্তর দেয়, আর ভয়েস ইনপুট ও আউটপুট সমর্থন করে।

✨ Key Features

🧠 Gemini 2.5 Flash — স্মার্ট AI Tutor (Bangla + English)

🌐 Hugging Face Backup — AI fallback for stable answers

📚 Offline JSON QnA System — ইন্টারনেট ছাড়াও কাজ করে

🧮 Safe Calculator — Math solver with sympy

🎤 Speech Recognition (STT) — বাংলায় ভয়েস ইনপুট

🔊 Text to Speech (TTS) — উত্তর শুনে নাও

⚡ Async Architecture — Fast, non-blocking, smooth performance

🧩 Streamlit UI — Clean, minimal & mobile-friendly



---

🏗️ Project Structure

EduSmart_AI/
│
├── app.py                # Main Streamlit Application
├── requirements.txt      # Dependencies list
├── README.md             # Documentation
└── json_data/            # Offline Q&A JSON files
     └── qna_basic.json


---

⚙️ Installation Guide

🔹 Step 1: Clone the Repository

git clone https://github.com/<your-username>/EduSmart-AI.git
cd EduSmart-AI

🔹 Step 2: Create Virtual Environment

python -m venv venv
source venv/bin/activate   # (Mac/Linux)
venv\Scripts\activate      # (Windows)

🔹 Step 3: Install Dependencies

pip install -r requirements.txt

🔹 Step 4: Add API Keys

Create a .env file (or use Streamlit Secrets) and add:

GEMINI_API_KEY=your_gemini_key_here
HUGGINGFACE_API_TOKEN=your_hf_key_here


---

🚀 Run the App Locally

streamlit run app.py

Then open your browser at
👉 http://localhost:8501


---

☁️ Deployment

🧭 Option 1 — Streamlit Cloud

1. Go to streamlit.io/cloud


2. Connect your GitHub repo


3. Select app.py as main file


4. Add Secrets under “Settings → Secrets”:

GEMINI_API_KEY=your_key
HUGGINGFACE_API_TOKEN=your_key



🤗 Option 2 — Hugging Face Spaces

1. Create a new Space


2. Choose Streamlit as SDK


3. Upload these files:

app.py

requirements.txt

json_data/

README.md



4. Add Environment Variables from Settings → Variables




---

📦 Requirements

streamlit
google-generativeai
sympy
httpx
gtts
SpeechRecognition
pydub
asyncio


---

🧠 Offline QnA Example (json_data/qna_basic.json)

[
  {"question": "noun", "answer": "A noun names a person, place, or thing. Example: Dhaka, book, love."},
  {"question": "ক্রিয়া", "answer": "ক্রিয়া হলো কাজ বা অবস্থাকে প্রকাশ করে। যেমন: খাওয়া, ঘুমানো।"},
  {"question": "triangle area formula", "answer": "Area = 1/2 × base × height"}
]


---

🧩 Future Features

🔍 Optical Character Recognition (OCR) — Image-based Q&A

💾 Chat Memory System

📊 Visual Math Solver (Graph plotting)

🧠 AI-driven Learning Recommendations



---

🧑‍💻 Author

Developed by: Zahid Hasan
Email: zh05698@gmail.com
Made with ❤️ for Bangladeshi Students
