import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
import sympy as sp
from sympy.plotting import vertical_line
import base64, os, re
from fpdf2 import FPDF
from datetime import datetime
from PIL import Image
import pytesseract
from langdetect import detect

# =============================
# 🔑 Gemini API Key Setup
# =============================
@st.cache_resource
def get_model(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password", placeholder="Enter your key...")

model = get_model(api_key) if api_key else None

# =============================
# 🎙 Voice I/O
# =============================
def speak(text, lang="bn"):
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save("temp.mp3")
        with open("temp.mp3", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        os.remove("temp.mp3")
        st.markdown(f"<audio src='data:audio/mp3;base64,{b64}' autoplay></audio>", unsafe_allow_html=True)
    except:
        st.markdown(f"""
        <script>
        if ('speechSynthesis' in window) {{
            var utt = new SpeechSynthesisUtterance("{text}");
            utt.lang = "{lang}";
            utt.rate = 1.0;
            speechSynthesis.speak(utt);
        }}
        </script>
        """, unsafe_allow_html=True)

def listen():
    r = sr.Recognizer()
    r.pause_threshold = 0.8
    try:
        with sr.Microphone() as src:
            st.info("🎧 Adjusting for ambient noise...")
            r.adjust_for_ambient_noise(src, duration=1)
            st.info("🎧 বলুন, আমি শুনছি...")
            audio = r.listen(src, timeout=10, phrase_time_limit=10)
        text = r.recognize_google(audio, language="bn-BD")
        if not any("\u0980" <= ch <= "\u09FF" for ch in text):
            text = r.recognize_google(audio, language="en-US")
        return text
    except sr.WaitTimeoutError:
        st.warning("🔇 সময় শেষ, কিছু শোনা যায়নি।")
        return ""
    except Exception:
        st.warning("🔇 শুনতে পারিনি, টেক্সট লিখে চেষ্টা করুন।")
        return ""

# =============================
# 🧮 Math Solver (cached core)
# =============================
@st.cache_data
def solve_math_core(expr):
    try:
        x = sp.Symbol('x')
        parsed = sp.sympify(expr)
        simplified = sp.simplify(parsed)
        if parsed.is_constant():
            return "const", simplified, [], sp.latex(simplified), parsed
        sol = sp.solve(parsed, x)
        real_sols = [s for s in sol if s.is_real]
        latex_expr = sp.latex(sp.simplify(parsed))
        return "eq", simplified, real_sols, latex_expr, parsed
    except:
        return None, None, None, None, None

# =============================
# 🎨 UI Config
# =============================
st.set_page_config(page_title="EduSmart AI Pro v5.4", page_icon="💡")
st.markdown("<h1 style='text-align:center;color:#38bdf8;'>EduSmart AI Pro v5.4</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>Chat • Math • Voice • OCR • PDF • Quiz (Beta)</h3>", unsafe_allow_html=True)

# =============================
# 💾 Session State
# =============================
defaults = {"chat": [], "quiz_mode": False, "quiz_text": "", "total_score": 0, "total_quizzes": 0}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# =============================
# 📸 OCR Section
# =============================
uploaded = st.file_uploader("📸 Upload math image (OCR Solver)")
if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Uploaded Image", use_column_width=True)
    text = pytesseract.image_to_string(img, config='--psm 6')
    text = re.sub(r'[^\w\s=+\-/*^()]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s*\^\s*', '^', text)
    text = text.replace(' x ', 'x').replace(' * ', '').replace(' = ', '=').replace(' + ', '+')
    if "=" not in text: text += " = 0"
    st.info(f"🧾 OCR Parsed: {text}")
    mode, simp, real_sols, latex_expr, parsed = solve_math_core(text)
    if mode:
        if mode == "const":
            st.success(f"🧮 Result: {simp}")
        elif real_sols:
            st.success(f"🧮 Simplified: {simp}\n✅ Real roots: {real_sols}")
        else:
            st.warning(f"🧮 Simplified: {simp}\n❌ No real solutions")
        st.latex(latex_expr)
        if real_sols and st.checkbox("📈 Show Graph?", key=f"ocr_plot_{text}"):
            try:
                low, high = min(real_sols)-1, max(real_sols)+1
                p = sp.plot(parsed, (sp.Symbol('x'), low, high), show=False)
                p[0].line_color='blue'; p[0].label='Equation'
                p.legend=True; p.legend_location='upper right'
                for i, root in enumerate(real_sols,1):
                    vline = sp.plot(vertical_line(root), show=False)
                    vline[0].line_color='red'; vline[0].line_style='--'
                    vline[0].label=f'Root {i}'
                    p.append(vline[0])
                st.pyplot(p._backend.fig)
            except Exception as e:
                st.warning(f"Graph Error: {e}")
        speak(str(simp))

# =============================
# 💬 Chat Interface
# =============================
for role, msg in st.session_state.chat:
    bubble = "user" if role=="user" else "ai"
    color = "#2563eb" if bubble=="user" else "#334155"
    st.markdown(f"<div style='background:{color};padding:10px 16px;border-radius:10px;margin:4px;color:white'>{msg}</div>", unsafe_allow_html=True)

prompt = st.chat_input("বার্তা লিখুন...")
voice_prompt = ""

if st.button("🎙️ ভয়েস ইনপুট দিন"):
    voice_prompt = listen()
    if voice_prompt:
        st.info(f"🎙️ আপনি বলেছেন: {voice_prompt}")
        prompt = voice_prompt

if prompt:
    st.session_state.chat.append(("user", prompt))
    st.markdown(f"<div style='background:#2563eb;color:white;padding:10px 16px;border-radius:10px;margin:4px'>{prompt}</div>", unsafe_allow_html=True)
    if not model:
        st.warning("⚠️ অনুগ্রহ করে Gemini API কী দিন।")
        st.stop()
    with st.spinner("🤖 EduSmart ভাবছে..."):
        mode, simp, real_sols, latex_expr, parsed = solve_math_core(prompt)
        if mode:
            if mode == "const":
                ans = f"🧮 Result: {simp}"
            elif real_sols:
                ans = f"🧮 Simplified: {simp}\n✅ Real roots: {real_sols}"
            else:
                ans = f"🧮 Simplified: {simp}\n❌ No real solutions"
            st.session_state.chat.append(("ai", ans))
            st.success(ans)
            st.latex(latex_expr)
            if real_sols and st.checkbox("📈 Show Graph?", key=f"chat_plot_{prompt}"):
                try:
                    low, high = min(real_sols)-1, max(real_sols)+1
                    p = sp.plot(parsed, (sp.Symbol('x'), low, high), show=False)
                    p[0].line_color='blue'; p[0].label='Equation'
                    p.legend=True; p.legend_location='upper right'
                    for i, root in enumerate(real_sols,1):
                        vline = sp.plot(vertical_line(root), show=False)
                        vline[0].line_color='red'; vline[0].line_style='--'
                        vline[0].label=f'Root {i}'
                        p.append(vline[0])
                    st.pyplot(p._backend.fig)
                except Exception as e:
                    st.warning(f"Graph error: {e}")
            speak(str(simp))
        else:
            response = model.generate_content(prompt).text
            st.session_state.chat.append(("ai", response))
            st.markdown(f"<div style='background:#334155;color:white;padding:10px 16px;border-radius:10px;margin:4px'>{response}</div>", unsafe_allow_html=True)
            try: speak(response, lang=detect(response))
            except: speak(response)

# =============================
# 📝 Quiz Mode (Beta)
# =============================
st.sidebar.markdown("---")
st.session_state.quiz_mode = st.sidebar.toggle("🧠 Quiz Mode", value=st.session_state.quiz_mode)
if st.session_state.quiz_mode:
    st.markdown("## 🧠 Quiz Mode (Beta)")
    if not st.session_state.quiz_text:
        topic = st.text_input("Quiz Topic:", placeholder="e.g. Algebra, Photosynthesis...")
        if st.button("Generate Quiz (3 Qs)"):
            if not model: st.warning("Need API key."); st.stop()
            prompt_q = f"Generate exactly 3 MCQs with 4 options (A-D) on '{topic}'. Include correct answers clearly."
            with st.spinner("Generating quiz..."):
                st.session_state.quiz_text = model.generate_content(prompt_q).text
                st.rerun()
    else:
        st.markdown(st.session_state.quiz_text)
        ans = st.text_area("✏️ Your Answers (e.g., 1:A, 2:C, 3:B)")
        if st.button("Check Answers"):
            grade_prompt = f"Grade this quiz:\n{st.session_state.quiz_text}\nUser answers: {ans}\nGive score out of 3."
            with st.spinner("Grading..."):
                grade = model.generate_content(grade_prompt).text
                st.success(grade)
                st.session_state.quiz_text = ""

# =============================
# 📄 PDF Export & Reset
# =============================
if st.button("📄 Save Chat as PDF"):
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
    pdf.cell(200,10,"EduSmart Chat",ln=True,align="C")
    for r,m in st.session_state.chat:
        pfx = "You:" if r=="user" else "AI:"
        pdf.multi_cell(0,8,f"{pfx} {m}"); pdf.ln(2)
    pdf.output("chat.pdf")
    with open("chat.pdf","rb") as f:
        st.download_button("⬇️ Download PDF", f, "EduSmart_Chat.pdf")

if st.button("🔄 Reset Chat"):
    if st.checkbox("Confirm reset?"):
        st.session_state.chat = []
        st.success("Chat cleared!")
        st.rerun()

st.caption("💡 EduSmart AI Pro v5.4 — Modular + Quiz Ready | by Zahid Hasan ⚡")
