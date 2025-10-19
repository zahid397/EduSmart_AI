import os
import json
import math
import socket
import tempfile
import asyncio
import streamlit as st
from gtts import gTTS
import speech_recognition as sr
from sympy import sympify, sqrt, pi
import google.generativeai as genai

# =============================
# 🔑 API Key & Model Config
# =============================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
GEMINI_MODEL_NAME = "gemini-2.5-flash"  # Use 2.5 flash

# =============================
# 🌐 Internet Check
# =============================
@st.cache_data(ttl=60)  # Cache check for 1 minute
def is_online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except:
        return False

# =============================
# 🎤 Speech to Text (Async)
# =============================
async def stt(audio_path):
    """Converts audio file to text asynchronously."""
    if not audio_path:
        return ""
    if not is_online():
        return "(Offline: Voice input unavailable)"
    
    def _recognize(path):
        # This is a blocking function, so we run it in an executor
        r = sr.Recognizer()
        with sr.AudioFile(path) as src:
            data = r.record(src)
        return r.recognize_google(data, language="bn-BD")

    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _recognize, audio_path)
    except Exception as e:
        return f"(STT Error: {e})"

# =============================
# 🔊 Text to Speech (Async)
# =============================
async def tts(text):
    """Converts text to speech asynchronously and returns the file path."""
    if not text:
        return None
    
    lang = "bn" if any('\u0980' <= c <= '\u09FF' for c in text) else "en"
    
    def _save_tts(tts_obj, path):
        # gTTS.save() is blocking
        tts_obj.save(path)

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            filename = fp.name
        
        tts_obj = gTTS(text=text, lang=lang, slow=False)
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _save_tts, tts_obj, filename)
        
        return filename
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

# =============================
# 🧮 Safe Calculator
# =============================
def calc(expr):
    """Safely evaluates a mathematical expression."""
    expr = expr.strip()
    if not expr:
        return ""

    # Only attempt if it looks like math
    if not any(c in expr for c in "+-*/^√π0123456789"):
        return ""
        
    expr = expr.replace("^", "**").replace("√", "sqrt").replace("π", "pi")
    
    try:
        result = sympify(expr).evalf()
        if result.is_number:
            return f"🧮 Answer = {result}"
        return "" # It was valid SymPy but not a calculable number
    except Exception:
        return "" # Failed to parse

# =============================
# 📘 Offline JSON Loader
# =============================
@st.cache_data  # Cache QnA data on first load
def load_qna():
    folder = "json_data"
    qna = []
    if not os.path.exists(folder):
        st.warning(f"Offline Q&A folder '{folder}' not found.")
        return []
    try:
        for f in os.listdir(folder):
            if f.endswith(".json"):
                with open(os.path.join(folder, f), encoding="utf-8") as file:
                    qna.extend(json.load(file))
    except Exception as e:
        st.error(f"Error loading local Q&A: {e}")
    return qna

QNA = load_qna()

def search_local(q):
    q = q.lower().strip()
    # Prioritize exact match
    for qa in QNA:
        if qa["question"].lower().strip() == q:
            return qa["answer"]
    # Fallback to 'in'
    for qa in QNA:
        if qa["question"].lower() in q:
            return qa["answer"]
    return ""

# =============================
# 🧠 Gemini Model (Async)
# =============================
async def gemini_answer(history, query):
    """Gets an answer from Gemini, including chat history for context."""
    if not GEMINI_KEY:
        return "(Gemini Error: API key not configured)"
    
    try:
        # Get or create the model in session state
        if "gemini_model" not in st.session_state:
            st.session_state.gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
        model = st.session_state.gemini_model
        
        # Build context
        messages = [
            {"role": "user", "parts": [qa["content"]]} 
            if qa["role"] == "user" else 
            {"role": "model", "parts": [qa["content"].split("\n", 1)[-1]]} # Remove our custom prefix
            for qa in history
        ]
        
        chat = model.start_chat(history=messages)
        prompt = f"Question: {query}\nAnswer clearly in Bangla and English with an example."
        
        r = await chat.send_message_async(prompt)
        return getattr(r, "text", "").strip()
    except Exception as e:
        return f"(Gemini Error: {e})"

# =============================
# 🤖 Main Response Logic (Async)
# =============================
async def get_response(history, query):
    """
    Main logic to get a response, following priority:
    1. Calculator
    2. Local Q&A
    3. AI (if online)
    4. Offline message
    Returns: (display_response, tts_text)
    """
    # 1. Calculator
    calc_res = calc(query)
    if calc_res:
        return calc_res, calc_res

    # 2. Offline QnA
    local_res = search_local(query)
    if local_res:
        full_res = f"📚 (Offline)\n{local_res}"
        return full_res, local_res

    # 3. Online AI
    if is_online():
        ai_res = await gemini_answer(history, query)
        if not ai_res.startswith("("): # Check for our error strings
            full_res = f"🌐 (AI)\n{ai_res}"
            return full_res, ai_res
        else:
            return ai_res, ai_res # Return the error message
    
    # 4. Offline Fallback
    return "📴 Offline. Connect to Internet or use offline Q&A.", "You are offline."

# =============================
# 💬 Streamlit UI
# =============================

# --- Page Config ---
st.set_page_config(page_title="EduSmart AI", page_icon="🎓", layout="centered")

st.markdown("""
    <style>
    /* Noto Sans Bengali font for consistent Bangla rendering */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;700&display=swap');
    
    body, .stTextInput, .stButton, .stMarkdown {
        font-family: 'Noto Sans Bengali', 'Arial', sans-serif;
    }
    .stChatInput {
        background-color: #ffffff;
    }
    /* Style for bot messages */
    [data-testid="stChatMessage"][data-streamed="false"] [data-testid="chatAvatarIcon-assistant"] + div {
        background-color: #e8f0fe; /* Light blue */
        border-radius: 10px;
    }
    /* Style for user messages */
    [data-testid="stChatMessage"][data-streamed="false"] [data-testid="chatAvatarIcon-user"] + div {
        background-color: #f0f0f0; /* Light grey */
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 EduSmart AI — Gemini Powered Tutor")

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audio" in message and message["audio"]:
            st.audio(message["audio"], format="audio/mp3")

# --- Reusable function to handle processing and UI update ---
async def handle_query(query):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Pass previous messages (except last one) for context
            history = st.session_state.messages[:-1]
            full_res, tts_res = await get_response(history, query)
            
            # Generate audio in parallel
            tts_task = asyncio.create_task(tts(tts_res))
            
            st.markdown(full_res)
            
            audio_path = await tts_task # Wait for TTS to finish
            if audio_path:
                st.audio(audio_path, format="audio/mp3", autoplay=True)
            
            # Add bot response to state
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_res,
                "audio": audio_path
            })

# --- Sidebar for Audio Input ---
st.sidebar.title("🎙️ Voice Input (বাংলা)")
audio_file = st.sidebar.file_uploader(
    "Upload your voice query", 
    type=["wav", "mp3", "m4a"]
)

if audio_file:
    with st.spinner("Transcribing audio..."):
        # Save uploaded file to a temporary path
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.type.split('/')[1]}") as tmp:
            tmp.write(audio_file.read())
            audio_path = tmp.name
        
        # Run STT
        user_query = asyncio.run(stt(audio_path))
        os.remove(audio_path) # Clean up temp file
        
        if user_query and not user_query.startswith("("):
            # Run the full query handling logic
            asyncio.run(handle_query(f"🗣️ {user_query}"))
        elif user_query:
            # Show STT Error
            st.error(user_query)
    # Clear the file uploader by rerunning
    st.rerun()

# --- Main Text Input ---
if prompt := st.chat_input("Ask (বাংলা / English / Math)"):
    asyncio.run(handle_query(prompt))

# --- Check API Key ---
if not GEMINI_KEY:
    st.error("GEMINI_API_KEY environment variable not set. AI features are disabled.")
    
