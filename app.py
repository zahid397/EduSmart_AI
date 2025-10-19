import streamlit as st
import json, random, csv, io
from difflib import SequenceMatcher
import language_tool_python  # Grammar check
from openai import OpenAI  # Optional AI explanations

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="EduSmart AI - Bangla Grammar Trainer",
    page_icon="💡",
    layout="wide",
)

# --- CSS + META ---
st.markdown("<meta name='viewport' content='width=device-width, initial-scale=1.0'>", unsafe_allow_html=True)

def get_css(theme):
    if theme == "dark":
        return """
        <style>
        .stApp { background-color: #0F172A; color: #F1F5F9; }
        .stButton > button { background-color:#1E40AF; color:white; border-radius:8px; padding:8px 16px; }
        .user-bubble { background-color:#1E40AF; color:#F1F5F9; padding:12px; border-radius:12px; margin:6px 0; }
        .bot-bubble { background-color:#334155; color:#F1F5F9; padding:12px; border-radius:12px; margin:6px 0; }
        </style>
        """
    else:
        return """
        <style>
        .stApp { background-color:#F9FAFB; color:#1E293B; }
        .stButton > button { background-color:#2563EB; color:white; border-radius:8px; padding:8px 16px; }
        .user-bubble { background-color:#E0E7FF; color:#1E293B; padding:12px; border-radius:12px; margin:6px 0; }
        .bot-bubble { background-color:#F1F5F9; color:#1E293B; padding:12px; border-radius:12px; margin:6px 0; }
        </style>
        """

# --- HEADER ---
try:
    st.image("edusmart_ai_logo.png", width=180)
except FileNotFoundError:
    st.markdown("### 💡 EduSmart AI")

st.markdown("<h1 style='text-align:center; color:#2563EB;'>EduSmart AI - বাংলা ব্যাকরণ সহায়ক</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Learn. Interact. Innovate.</p>", unsafe_allow_html=True)
st.write("---")

# --- SIDEBAR ---
st.sidebar.header("🔧 Options")
theme = st.sidebar.selectbox("🌙 Theme", ["light", "dark"])
st.markdown(get_css(theme), unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("📂 Upload Bangla Grammar JSONL File", type=["jsonl"])
use_ai = st.sidebar.checkbox("🤖 Enable AI Explanation (Optional)")
openai_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password") if use_ai else None
st.sidebar.markdown("---")

# --- LOADERS ---
@st.cache_data
def load_data(file):
    lines = [l.strip() for l in file.read().decode("utf-8").split("\n") if l.strip()]
    return [json.loads(l) for l in lines]

def fuzzy_match(q, data, threshold=0.6):
    best = max(data, key=lambda x: SequenceMatcher(None, q.lower(), x["question"].lower()).ratio())
    if SequenceMatcher(None, q.lower(), best["question"].lower()).ratio() > threshold:
        return best
    return None

# Grammar Tool with Try-Except (if not installed)
try:
    tool = language_tool_python.LanguageTool('bn')
except:
    tool = None
    st.sidebar.warning("⚠️ LanguageTool not available. Install: pip install language-tool-python")

# --- MAIN ---
if uploaded_file:
    data = load_data(uploaded_file)
    st.success(f"✅ মোট প্রশ্ন: {len(data)}")

    if "score" not in st.session_state:
        st.session_state.score = 0
        st.session_state.badges = []
        st.session_state.scores_history = []
        st.session_state.user_answers = []  # New: Track user answers for CSV

    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "🧠 Quiz", "📖 Browse", "📊 Progress"])

    # 💬 Chat
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("🗣️ প্রশ্ন লিখো:")
        with col2:
            audio = st.audio_input("🎤 Voice Input")
            if audio:
                st.audio(audio)
                st.info("🔊 Voice received (transcription integration possible)")

        if query:
            # Grammar feedback with try-except
            if tool:
                errors = tool.check(query)
                if errors:
                    st.warning(f"📝 Grammar Tip: {errors[0].message}")
            else:
                st.info("📝 Grammar check available with LanguageTool install.")

            match = next((x for x in data if query.lower() in x["question"].lower()), fuzzy_match(query, data))
            st.markdown(f"<div class='user-bubble'><b>তুমি:</b> {query}</div>", unsafe_allow_html=True)
            if match:
                ans = match["answer"]
                if use_ai and openai_key:
                    client = OpenAI(api_key=openai_key)
                    prompt = f"বাংলায় সহজভাবে ব্যাখ্যা করো: {match['question']} → {ans}। উদাহরণসহ বোলো।"
                    res = client.chat.completions.create(model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}])
                    ans = res.choices[0].message.content
                st.markdown(f"<div class='bot-bubble'><b>EduSmart:</b> {ans}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='bot-bubble'>দুঃখিত 😕 উত্তর পাইনি।</div>", unsafe_allow_html=True)

    # 🧠 Quiz
    with tab2:
        if st.button("🚀 Start New Quiz"):
            st.session_state.quiz = random.sample(data, 5)
            st.session_state.index = 0
            st.session_state.score = 0
            st.session_state.user_answers = []  # Reset user answers

        if "quiz" in st.session_state:
            idx = st.session_state.index
            if idx < 5:
                q = st.session_state.quiz[idx]
                st.markdown(f"**প্রশ্ন {idx + 1}/5:** {q['question']}")
                options = [q["answer"][:20] + " (সঠিক)", "ভুল অপশন ১", "ভুল অপশন ২"]
                random.shuffle(options)
                ans = st.radio("উত্তর:", options, key=f"q_{idx}")
                if st.button("Submit", key=f"s_{idx}"):
                    st.session_state.user_answers.append(ans)  # Track user choice
                    if "(সঠিক)" in ans:
                        st.session_state.score += 1
                        st.success("✅ সঠিক উত্তর!")
                    else:
                        st.error("❌ ভুল উত্তর!")
                    st.session_state.index += 1
                    st.rerun()
            else:
                s = st.session_state.score
                st.success(f"🎉 Quiz শেষ! স্কোর: {s}/5")
                st.session_state.scores_history.append(s)
                if s >= 4:
                    st.balloons()
                    st.session_state.badges.append("🏅 Grammar Master")
                
                # Enhanced CSV with User Answers
                csv_buf = io.StringIO()
                writer = csv.writer(csv_buf)
                writer.writerow(["Question", "Your Answer", "Correct Answer"])
                for i, qa in enumerate(st.session_state.quiz):
                    writer.writerow([qa["question"], st.session_state.user_answers[i], qa["answer"]])
                st.download_button("📥 Download Results", csv_buf.getvalue().encode('utf-8'), "EduSmart_Score.csv", "text/csv")
                
                # New: Try Again Button
                if st.button("🔄 Try Again"):
                    del st.session_state.quiz
                    st.rerun()

    # 📖 Browse
    with tab3:
        if st.checkbox("Show All Questions"):
            for i, qa in enumerate(data, 1):
                with st.expander(f"{i}. {qa['question'][:60]}..."):
                    st.markdown(f"**উত্তর:** {qa['answer']}")

    # 📊 Progress Dashboard
    with tab4:
        st.subheader("📊 তোমার অগ্রগতি")
        st.metric("Total Quizzes", len(st.session_state.scores_history))
        avg = sum(st.session_state.scores_history) / len(st.session_state.scores_history) if st.session_state.scores_history else 0
        st.metric("Average Score", f"{avg:.2f}/5")
        if st.session_state.scores_history:
            st.bar_chart(st.session_state.scores_history)
        if st.session_state.badges:
            st.success(f"🏆 Badges: {' '.join(st.session_state.badges)}")

else:
    st.info("📂 শুরু করতে তোমার JSONL ফাইল আপলোড করো।")
    st.code('{"question": "বাংলায় বিশেষ্য কী?", "answer": "বিশেষ্য হলো কোনো ব্যক্তি, স্থান বা বস্তুর নাম।"}', language="json")

# --- FOOTER ---
st.markdown("""
---
<p style='text-align:center; color:gray;'>
🚀 Developed by <b>Zahid Hasan</b> | Powered by <b>EduSmart AI</b><br>
🌍 <b>Innovation World Cup Bangladesh 2026 - National Finalist 🇧🇩</b> | Register: <a href="https://forms.gle/nh6WBfH4nd6GMCC2A" style="color:#2563EB;">Deadline: 20 Oct</a>
</p>
""", unsafe_allow_html=True)
