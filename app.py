import streamlit as st
import json, random, csv, io, sympy as sp, tempfile, requests
from difflib import SequenceMatcher
import google.generativeai as genai
import language_tool_python
import speech_recognition as sr

# --- PAGE CONFIG ---
st.set_page_config(page_title="EduSmart AI Pro", page_icon="💡", layout="wide")

# --- HEADER ---
try:
    st.image("edusmart_ai_logo.png", width=180)
except:
    st.markdown("<h2 style='text-align:center; color:#2563EB;'>💡 EduSmart AI Pro</h2>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#2563EB;'>EduSmart AI Pro - Learn • Solve • Search</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>🇧🇩 Bangla | English | Math | Voice | AI | Web Search</p>", unsafe_allow_html=True)
st.write("---")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Settings")
theme = st.sidebar.selectbox("🌙 Theme", ["Light", "Dark"])

api_key = st.sidebar.text_input("🔑 Gemini 2.5 Flash API Key", type="password")
if api_key:
    genai.configure(api_key=api_key)
use_ai = st.sidebar.checkbox("🤖 Enable Gemini 2.5 Flash AI")
use_web = st.sidebar.checkbox("🌐 Enable Google Search Fallback")
google_key = st.sidebar.text_input("🔑 Google Custom Search API Key", type="password")
google_cx = st.sidebar.text_input("🔍 Google Search Engine ID (CX)", type="default")

uploaded_file = st.sidebar.file_uploader("📂 Upload Bangla Grammar JSONL File", type=["jsonl"])

# --- THEME STYLE ---
st.markdown(f"""
<style>
.stApp {{
    background-color: {"#F9FAFB" if theme=="Light" else "#0F172A"};
    color: {"#1E293B" if theme=="Light" else "#F1F5F9"};
}}
.stButton > button {{
    background-color: {"#2563EB" if theme=="Light" else "#1E40AF"};
    color: white; border-radius:8px; padding:8px 16px;
}}
.user-bubble {{background-color:#E0E7FF; padding:10px; border-radius:10px; margin:5px 0;}}
.bot-bubble {{background-color:#F1F5F9; padding:10px; border-radius:10px; margin:5px 0;}}
</style>
""", unsafe_allow_html=True)

# --- HELPERS ---
def detect_subject(text):
    text_l = text.lower()
    if any(w in text_l for w in ["যোগ", "বিয়োগ", "গুণ", "ভাগ", "x", "=", "+", "-", "*", "/", "solve"]):
        return "Math"
    elif any(w in text_l for w in ["noun", "verb", "adjective", "grammar", "tense", "article"]):
        return "English"
    elif any(w in text_l for w in ["বিশেষ্য", "ক্রিয়া", "বিশেষণ", "বাক্য", "কারক", "অনুজ্ঞা"]):
        return "Bangla"
    else:
        return "General"

@st.cache_data
def load_data(file):
    lines = [l.strip() for l in file.read().decode("utf-8").split("\n") if l.strip()]
    return [json.loads(l) for l in lines]

def fuzzy_match(q, data, threshold=0.6):
    best = max(data, key=lambda x: SequenceMatcher(None, q.lower(), x["question"].lower()).ratio())
    if SequenceMatcher(None, q.lower(), best["question"].lower()).ratio() > threshold:
        return best
    return None

def solve_math(expr):
    try:
        x = sp.Symbol('x')
        sol = sp.solve(expr, x)
        if sol:
            return f"✅ Solution: x = {sol}"
        result = sp.sympify(expr).evalf()
        return f"✅ Result: {result}"
    except Exception as e:
        return f"❌ Invalid math: {e}"

def google_search(query):
    """Fallback search using Google Custom Search API"""
    if not (google_key and google_cx):
        return "⚠️ Google Search API not configured."
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={google_key}&cx={google_cx}"
        res = requests.get(url).json()
        if "items" in res:
            top = res["items"][0]
            return f"🔗 **{top['title']}**\n\n{top['snippet']}\n\n[Read more]({top['link']})"
        else:
            return "❌ No web results found."
    except Exception as e:
        return f"⚠️ Web search error: {e}"

def transcribe_audio(audio_file):
    r = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_file.getvalue())
        tmp.flush()
        with sr.AudioFile(tmp.name) as source:
            audio = r.record(source)
            try:
                return r.recognize_google(audio, language="bn-BD")
            except:
                return "🎤 অডিও বোঝা যায়নি।"

# --- GRAMMAR TOOL ---
try:
    tool = language_tool_python.LanguageTool('bn')
except:
    tool = None
    st.sidebar.warning("⚠️ Grammar checker disabled. Install: pip install language-tool-python")

# --- MAIN ---
if uploaded_file:
    data = load_data(uploaded_file)
    st.success(f"✅ Loaded {len(data)} Questions")

    if 'scores_history' not in st.session_state:
        st.session_state.scores_history = []
        st.session_state.badges = []

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "🧠 Quiz", "📖 Browse", "🎙️ Voice", "📊 Progress"])

    # 💬 CHAT
    with tab1:
        query = st.text_input("💡 Enter your question:")
        if 'voice_text' in st.session_state and not query:
            query = st.session_state.voice_text
            st.info(f"🎤 Voice input: {query}")

        if query:
            subject = detect_subject(query)
            st.info(f"🎯 Subject: {subject}")

            if subject in ["Bangla", "English"] and tool:
                errs = tool.check(query)
                if errs:
                    st.warning(f"📝 Grammar Tip: {errs[0].message}")

            if subject == "Math":
                ans = solve_math(query)
                st.markdown(f"<div class='bot-bubble'><b>Math Solver:</b> {ans}</div>", unsafe_allow_html=True)

            elif subject in ["Bangla", "English"]:
                match = next((x for x in data if query.lower() in x["question"].lower()), fuzzy_match(query, data))
                if match:
                    st.markdown(f"<div class='bot-bubble'><b>{subject} Answer:</b> {match['answer']}</div>", unsafe_allow_html=True)
                else:
                    if use_ai and api_key:
                        try:
                            model = genai.GenerativeModel("gemini-2.5-flash")
                            r = model.generate_content(f"Explain this {subject.lower()} question in simple {subject.lower()}: {query}")
                            st.markdown(f"<div class='bot-bubble'><b>AI ({subject}):</b> {r.text}</div>", unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"AI Error (e.g., quota): {e}")
                    elif use_web:
                        web_ans = google_search(query)
                        st.markdown(f"<div class='bot-bubble'><b>🌐 Web Result:</b><br>{web_ans}</div>", unsafe_allow_html=True)
                    else:
                        st.warning("No answer found.")

            else:
                if use_ai and api_key:
                    try:
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        r = model.generate_content(f"Answer clearly in Bangla or English: {query}")
                        st.markdown(f"<div class='bot-bubble'><b>AI:</b> {r.text}</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"AI Error (e.g., quota): {e}")
                elif use_web:
                    web_ans = google_search(query)
                    st.markdown(f"<div class='bot-bubble'><b>🌐 Web:</b><br>{web_ans}</div>", unsafe_allow_html=True)
                else:
                    st.warning("No AI or Web fallback enabled!")

    # 🎙️ VOICE
    with tab4:
        st.subheader("🎤 Speak your question:")
        audio = st.audio_input("Record:")
        if audio:
            text = transcribe_audio(audio)
            st.session_state.voice_text = text
            st.success(f"🗣️ Transcribed: {text}")
            st.info("Go to Chat tab to see answer!")

    # 🧠 QUIZ
    with tab2:
        if st.button("🚀 Start Quiz"):
            st.session_state.quiz = random.sample(data, 5)
            st.session_state.index = 0
            st.session_state.score = 0
            st.session_state.user_answers = []

        if "quiz" in st.session_state:
            i = st.session_state.index
            if i < 5:
                q = st.session_state.quiz[i]
                st.write(f"**Q{i+1}/5:** {q['question']}")
                opts = [q["answer"][:20]+" (Correct)", "Wrong 1", "Wrong 2", "Wrong 3"]
                random.shuffle(opts)
                ans = st.radio("Choose:", opts, key=f"ans_{i}")
                if st.button("Submit", key=f"s_{i}"):
                    st.session_state.user_answers.append(ans)
                    if "(Correct)" in ans:
                        st.session_state.score += 1
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Wrong! Correct: {q['answer']}")
                    st.session_state.index += 1
                    st.rerun()
            else:
                s = st.session_state.score
                st.success(f"🎉 Quiz done! Score: {s}/5")
                st.session_state.scores_history.append(s)
                if s >= 4:
                    st.balloons()
                    st.session_state.badges.append("🏅 Quiz Master")

                csv_buf = io.StringIO()
                writer = csv.writer(csv_buf)
                writer.writerow(["Question", "Your Answer", "Correct Answer"])
                for j, qa in enumerate(st.session_state.quiz):
                    writer.writerow([qa["question"], st.session_state.user_answers[j], qa["answer"]])
                st.download_button("📥 Download Results", csv_buf.getvalue().encode('utf-8'), "EduSmart_Quiz.csv", "text/csv")

                if st.button("🔄 New Quiz"):
                    del st.session_state.quiz
                    st.rerun()

    # 📖 BROWSE
    with tab3:
        if st.checkbox("📚 Show All Questions"):
            for i, qa in enumerate(data, 1):
                with st.expander(f"{i}. {qa['question'][:60]}..."):
                    st.markdown(f"**Answer:** {qa['answer']}")

    # 📊 PROGRESS
    with tab5:
        st.subheader("📊 Your Progress")
        if st.session_state.scores_history:
            st.metric("Total Quizzes", len(st.session_state.scores_history))
            avg = sum(st.session_state.scores_history)/len(st.session_state.scores_history)
            st.metric("Average Score", f"{avg:.1f}/5")
            st.bar_chart(st.session_state.scores_history)
        if st.session_state.badges:
            st.success("🏆 " + ", ".join(st.session_state.badges))
        else:
            st.info("Earn badges by scoring 80%+ in quiz!")
        if st.button("🗑️ Reset Progress"):
            st.session_state.scores_history = []
            st.session_state.badges = []
            st.rerun()

else:
    st.info("📂 Upload your JSONL file to start learning.")
    st.code('{"question": "বাংলায় বিশেষ্য কী?", "answer": "বিশেষ্য হলো কোনো ব্যক্তি, স্থান বা বস্তুর নাম।"}', language="json")

# --- FOOTER ---
st.markdown("""
---
<p style='text-align:center; color:gray;'>
🚀 Developed by <b>Zahid Hasan</b> | Powered by <b>Gemini 2.5 Flash + Google Search</b><br>
🌍 National Finalist - Innovation World Cup Bangladesh 2026 🇧🇩 | <a href="https://forms.gle/nh6WBfH4nd6GMCC2A" style="color:#2563EB;">Register Now (Deadline: 20 Oct)</a>
</p>
""", unsafe_allow_html=True)
