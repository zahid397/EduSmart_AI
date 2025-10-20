# ============================================
# EduSmart AI Pro v5.7 — Final Cloud Edition ✅
# ============================================
import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
import base64, os, re, json
from gtts import gTTS
from fpdf import FPDF     # ✅ Fixed import for Streamlit Cloud
from datetime import datetime
from langdetect import detect
from PIL import Image
import pytesseract
import sympy as sp
from sympy.plotting import plot
import matplotlib
matplotlib.use("Agg")
import platform, os
IS_CLOUD = "streamlit" in platform.node().lower() or os.environ.get("STREAMLIT_RUNTIME", "")
if not IS_CLOUD:
    if st.button("🎙️ ভয়েস ইনপুট দিন"):
        voice_input = listen()
        if voice_input:
            st.info(f"🎙️ আপনি বলেছেন: {voice_input}")
            prompt = voice_input
else:
    st.warning("🎙️ ভয়েস ইনপুট Streamlit Cloud-এ কাজ করে না। লোকাল কম্পিউটারে চালিয়ে দেখুন।")

# ---------- Gemini Setup ----------
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
def speak(text, lang="bn"):
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save("temp.mp3")
        with open("temp.mp3", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        os.remove("temp.mp3")
        st.markdown(
            f"<audio autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>",
            unsafe_allow_html=True,
        )
    except Exception:
        # Browser fallback
        st.markdown(
            f"""
            <script>
            if ('speechSynthesis' in window) {{
                var utt = new SpeechSynthesisUtterance({json.dumps(text)});
                utt.lang = '{lang}';
                utt.rate = 1.0;
                speechSynthesis.speak(utt);
            }}
            </script>
            """,
            unsafe_allow_html=True,
        )

def listen():
    r = sr.Recognizer()
    r.pause_threshold = 0.8
    try:
        with sr.Microphone() as src:
            st.info("🎧 Adjusting for ambient noise...")
            r.adjust_for_ambient_noise(src, duration=1)
            st.info("🎧 বলুন, আমি শুনছি...")
            audio = r.listen(src, timeout=10, phrase_time_limit=10)
        return r.recognize_google(audio, language="bn-BD")
    except Exception as e:
        st.warning(f"🎙️ ভয়েস ইনপুট ব্যর্থ: {e}")
        return ""

# ---------- Math Solver ----------
@st.cache_data
def solve_math(expr):
    try:
        x = sp.Symbol("x")
        parsed = sp.sympify(expr)
        simplified = sp.simplify(parsed)
        if parsed.is_constant():
            return f"🧮 Result: {simplified}", sp.latex(simplified), []
        sol = sp.solve(parsed, x)
        real_sols = [s for s in sol if s.is_real]
        latex_expr = sp.latex(parsed)
        if real_sols:
            msg = f"🧮 Simplified: {simplified}\n✅ Real solutions: {real_sols}"
        elif sol:
            msg = f"🧮 Simplified: {simplified}\n❌ No real solutions (complex: {sol})"
        else:
            msg = f"🧮 Simplified: {simplified}\n❌ No solution"
        return msg, latex_expr, real_sols
    except Exception as e:
        return f"⚠️ Math error: {e}", None, []

# ---------- UI ----------
st.set_page_config(page_title="EduSmart AI Pro", page_icon="💡", layout="wide")
st.markdown(
    """
    <style>
    .stApp{background:linear-gradient(135deg,#020617,#0f172a,#1e293b);color:#f8fafc;font-family:'Poppins',sans-serif;}
    .chat-bubble-user{background:#2563eb;color:#fff;padding:10px 16px;border-radius:16px 16px 4px 16px;margin:6px 0;max-width:85%;}
    .chat-bubble-ai{background:#334155;color:#f8fafc;padding:10px 16px 16px 4px;margin:6px 0;max-width:85%;}
    h1,h3{text-align:center;color:#38bdf8;}
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown("<h1>EduSmart AI Pro ⚡ Supreme+ Edition 📈</h1>", unsafe_allow_html=True)
st.markdown("<h3>Learn • Solve • Speak • Visualize</h3>", unsafe_allow_html=True)

# ---------- Session ----------
for k, v in {"chat": [], "quiz_mode": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- OCR ----------
uploaded = st.file_uploader("📸 Upload a Math Image (Optional)")
if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Uploaded Image", use_column_width=True)
    text = pytesseract.image_to_string(img)
    text = re.sub(r"[^\w\s=+*/^()-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" x ", "x").replace(" = ", "=").replace(" + ", "+")
    text = re.sub(r"\s*\^\s*", "^", text)
    if "=" not in text:
        text += " = 0"
    st.info(f"🧾 Detected Equation: {text}")
    msg, latex_expr, real_sols = solve_math(text)
    st.success(msg)
    if latex_expr:
        st.latex(latex_expr)
    if real_sols and st.checkbox("📈 Show Graph?", key=f"plot_{text}"):
        try:
            low, high = min(real_sols) - 1, max(real_sols) + 1
            p = plot(sp.sympify(text.replace("=0", "")), (sp.Symbol("x"), low, high), show=False)
            p[0].line_color = "blue"
            p[0].label = "Equation"
            for i, root in enumerate(real_sols):
                vline = plot(sp.Symbol("x") - root, show=False)
                vline[0].line_color = "red"
                vline[0].line_style = "--"
                vline[0].label = f"Root {i+1}"
                p.append(vline[0])
            p.legend = True
            p.legend_location = "upper right"
            st.pyplot(p._backend.fig)
        except Exception as e:
            st.error(f"Plot Error: {e}")

# ---------- Chat ----------
for role, msg in st.session_state.chat:
    css = "chat-bubble-user" if role == "user" else "chat-bubble-ai"
    st.markdown(f"<div class='{css}'>{msg}</div>", unsafe_allow_html=True)

prompt = st.chat_input("বার্তা লিখুন...")
if st.button("🎙️ ভয়েস ইনপুট দিন"):
    voice_input = listen()
    if voice_input:
        st.info(f"🎙️ আপনি বলেছেন: {voice_input}")
        prompt = voice_input

if prompt:
    st.session_state.chat.append(("user", prompt))
    st.markdown(f"<div class='chat-bubble-user'>{prompt}</div>", unsafe_allow_html=True)
    if not model:
        st.warning("⚠️ API Key দিন।")
        st.stop()
    with st.spinner("🤖 EduSmart ভাবছে..."):
        try:
            response = model.generate_content(prompt).text
            st.session_state.chat.append(("ai", response))
            st.markdown(f"<div class='chat-bubble-ai'>{response}</div>", unsafe_allow_html=True)
            try:
                lang = detect(response)
            except:
                lang = "bn"
            speak(response, lang)
        except Exception as e:
            st.error(f"❌ ত্রুটি: {e}")

# ---------- Math Input ----------
st.markdown("---")
expr = st.text_input("🧮 Enter math expression (optional):", placeholder="e.g., x^2 - 4")
if expr:
    msg, latex_expr, real_sols = solve_math(expr)
    st.success(msg)
    if latex_expr:
        st.latex(latex_expr)
    if real_sols and st.checkbox("📈 Show Graph?", key=f"plot_{expr}"):
        try:
            low, high = min(real_sols) - 1, max(real_sols) + 1
            p = plot(sp.sympify(expr), (sp.Symbol("x"), low, high), show=False)
            p[0].line_color = "blue"
            for i, root in enumerate(real_sols):
                vline = plot(sp.Eq(sp.Symbol("x"), root), show=False)
                vline[0].line_color = "red"
                vline[0].line_style = "--"
                vline[0].label = f"Root {i+1}"
                p.append(vline[0])
            p.legend = True
            p.legend_location = "upper right"
            st.pyplot(p._backend.fig)
        except Exception as e:
            st.error(f"Plot Error: {e}")

# ---------- PDF Export ----------
st.markdown("---")
if st.button("📄 Save Chat as PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "EduSmart AI Pro Chat History", ln=True, align="C")
    pdf.cell(200, 10, f"Saved: {datetime.now()}", ln=True)
    pdf.ln(10)
    for role, msg in st.session_state.chat:
        prefix = "👤 You:" if role == "user" else "🤖 AI:"
        pdf.multi_cell(0, 8, f"{prefix} {msg}")
        pdf.ln(2)
    pdf.output("chat.pdf")
    with open("chat.pdf", "rb") as f:
        st.download_button("⬇️ Download PDF", f, "EduSmart_Chat.pdf")
